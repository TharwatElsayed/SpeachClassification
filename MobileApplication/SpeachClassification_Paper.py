from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.animation import Animation
from kivy.uix.widget import Widget
from threading import Thread
import speech_recognition as sr

# --- Transformers Pipeline ---
from transformers import pipeline
classifier = pipeline("text-classification", model="Tharwat-Elsayed/SpeachClassification")

# --- Custom label mapping ---
LABEL_MAP = {
    "LABEL_0": "Neutral Speech",
    "LABEL_1": "Offensive Speech",
    "LABEL_2": "Hate Speech"
}


KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(30)

    MDLabel:
        id: status_label
        text: "Press to record"
        halign: "center"
        font_style: "H5"

    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'

        FloatLayout:
            size_hint: None, None
            size: dp(200), dp(200)

            # Two pulse layers
            Widget:
                id: pulse1
                size_hint: None, None
                size: dp(120), dp(120)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                canvas.before:
                    Color:
                        rgba: 0, 0.6, 1, 0.3
                    Ellipse:
                        pos: self.pos
                        size: self.size

            Widget:
                id: pulse2
                size_hint: None, None
                size: dp(120), dp(120)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                canvas.before:
                    Color:
                        rgba: 0, 0.6, 1, 0.15
                    Ellipse:
                        pos: self.pos
                        size: self.size

            MDIconButton:
                id: mic_button
                icon: "microphone"
                user_font_size: "48sp"
                md_bg_color: 0, 0.6, 1, 1
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                on_release: app.toggle_recording()
'''


class SpeechApp(MDApp):
    def build(self):
        self.title = "Voice Recorder with Classification"
        self.theme_cls.primary_palette = "Blue"
        self.is_recording = False
        self.root = Builder.load_string(KV)
        return self.root

    # ------------------------------- Record Button -------------------------------
    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.root.ids.status_label.text = "Listening..."
            self.root.ids.mic_button.md_bg_color = (1, 0, 0, 1)
            self.start_pulse_animation()
            Thread(target=self.record_voice, daemon=True).start()
        else:
            self.is_recording = False
            self.root.ids.status_label.text = "Processing..."
            self.stop_pulse_animation()

    # ------------------------------- Pulse Animation -------------------------------
    def start_pulse_animation(self):
        for i, pulse in enumerate([self.root.ids.pulse1, self.root.ids.pulse2]):
            pulse.opacity = 0
            self.animate_pulse(pulse, delay=i * 0.8)

    def animate_pulse(self, pulse, delay=0):
        def loop(*_):
            if self.is_recording:
                pulse.size = (120, 120)
                anim = Animation(size=(200, 200), opacity=0, duration=1.8, t='in_out_quad')
                anim += Animation(size=(120, 120), opacity=0.3, duration=0)
                anim.bind(on_complete=lambda *_: loop())
                anim.start(pulse)
        Clock.schedule_once(loop, delay)

    def stop_pulse_animation(self):
        for pulse in [self.root.ids.pulse1, self.root.ids.pulse2]:
            Animation.cancel_all(pulse)
            pulse.opacity = 0
            pulse.size = (120, 120)
        self.root.ids.mic_button.md_bg_color = (0, 0.6, 1, 1)

    # ------------------------------- Speech + Classification -------------------------------
    def record_voice(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                text = recognizer.recognize_google(audio_data, language="en-US")

                # --- Classification ---
                result = classifier(text)[0]
                raw_label = result["label"]
                score = float(result["score"])

                # Convert LABEL_X → human readable
                readable_label = LABEL_MAP.get(raw_label, raw_label)

                output = (
                    f"Recognized:\n{text}\n\n"
                    f"Classification:\n{readable_label} — {score:.2f}"
                )

                self.update_label(output)

            except sr.UnknownValueError:
                self.update_label("Sorry, I couldn't understand.")
            except sr.RequestError:
                self.update_label("Network error. Check your Internet.")
            except Exception as e:
                self.update_label(f"Error: {e}")

        self.reset_ui()

    # ------------------------------- UI Updates -------------------------------
    @mainthread
    def update_label(self, text):
        self.root.ids.status_label.text = text
        print(text)

    @mainthread
    def reset_ui(self):
        self.is_recording = False
        self.stop_pulse_animation()
        self.root.ids.mic_button.md_bg_color = (0, 0.6, 1, 1)


if __name__ == "__main__":
    SpeechApp().run()
