import alsaseq
import time

from queue import Queue, Empty

from pyseq.events import parse_event

CTRL_CHANNEL = 8

# Main controller notes
PAGE_UP = 41
PAGE_DN = 73
SCALE_UP = 42
SCALE_DN = 74
SPEED_UP = 43
SPEED_DN = 75
EXIT = 106


class MidiInCtrl:

    def __init__(self):
        self.in_q = Queue()
        self.queues = []

    def subscribe(self, q):
        self.queues.append(q)
    
    def publish(self, message):
        for q in self.queues:
            q.put(message)

    def receive(self, debug=False):
        running = True
        if debug:
            print("run receiver")
        while running:
            # Read the queue
            try:
                msg = self.in_q.get_nowait()
            except Empty:
                pass
            else:
                ctrl, idx, value = msg
                if ctrl == "exit":
                    self.running = False
            # Event types:
            # https://www.alsa-project.org/alsa-doc/alsa-lib/seq__event_8h_source.html
            evt = parse_event(*alsaseq.input(), debug=debug)
            if evt["channel"] == CTRL_CHANNEL:
                # Main controller event
                if evt["control"]:
                    control = evt["control"]["control"]
                    value = evt["control"]["value"]
                    if debug:
                        print("control", evt)
                    if 13 <= control <= 20:
                        self.publish(("cc1", control - 13, value))
                    if 29 <= control <= 36:
                        self.publish(("cc2", control - 29, value))
                    if 49 <= control <= 56:
                        self.publish(("cc3", control - 49, value))
                    if 77 <= control <= 84:
                        self.publish(("cc4", control - 77, value))
                elif evt["note"]:
                    note = evt["note"]["note"]
                    if debug:
                        print(evt)
                    if note == PAGE_UP:
                        self.publish(("pagechange", 0, 1))
                    if note == PAGE_DN:
                        self.publish(("pagechange", 0, -1))
                    if note == SCALE_UP:
                        self.publish(("scalechange", 0, 1))
                    if note == SCALE_DN:
                        self.publish(("scalechange", 0, -1))
                    if note == SPEED_UP:
                        self.publish(("speedchange", 0, 10))
                    if note == SPEED_DN:
                        self.publish(("speedchange", 0, -10))
                    if note == EXIT:
                        self.publish(("exit", 0, 0))
                        running = False
                    self.publish(("message", None, str(evt)))
            elif evt["note"]:
                # Root note change from another controller
                if debug:
                    print("note", evt)
                note = data[1]
                self.publish(("root", 0, evt["note"]["note"]))

