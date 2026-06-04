import tkinter as tk
from tkinter import messagebox, Toplevel
from src.audio_engine import AudioEngine
from src.data_collector import DataCollector
from src.typing_interface import TypingApp
import os

def show_results_popup(participant_id, data_collector, root):
    """Creates a popup at the end of the test to decide the fate of the data."""
    summary_win = Toplevel(root)
    summary_win.title("Trial Complete")
    summary_win.geometry("300x250")
    summary_win.grab_set() # Forces focus on this window

    # Calculate quick stats for the researcher
    total = len(data_collector.results)
    avg_lat = sum(d['latency_ms'] for d in data_collector.results) / total if total > 0 else 0

    tk.Label(summary_win, text=f"Results for Subject {participant_id}", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(summary_win, text=f"Alarms Triggered: {total}").pack()
    tk.Label(summary_win, text=f"Average Latency: {avg_lat:.2f} ms").pack(pady=5)

    def save_and_exit():
        data_collector.save_to_csv()
        print(f"SUCCESS: Data for {participant_id} saved.")
        root.quit() # End the whole program

    def restart_trial():
        if messagebox.askyesno("Confirm Restart", "This will PERMANENTLY DELETE current data. Restart?"):
            summary_win.destroy()
            root.destroy()
            show_setup_ui() # Loop back to the very beginning

    tk.Button(summary_win, text="SAVE & EXIT", command=save_and_exit, bg="green", fg="white", width=20).pack(pady=10)
    tk.Button(summary_win, text="DISCARD & RESTART", command=restart_trial, bg="red", fg="white", width=20).pack(pady=5)

def launch_experiment(participant_id, is_musician, setup_window):
    setup_window.destroy()
    os.makedirs("data/raw", exist_ok=True)
    
    root = tk.Tk()
    audio_engine = AudioEngine()
    data_collector = DataCollector(participant_id, is_musician)
    app = TypingApp(root, audio_engine, data_collector)
    
    # We change the 'X' button behavior so it doesn't auto-save
    def on_closing():
        if messagebox.askyesno("Quit", "Test in progress. Show results summary?"):
            show_results_popup(participant_id, data_collector, root)
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def show_setup_ui():
    setup = tk.Tk()
    setup.title("Researcher Login")
    setup.geometry("300x250")

    tk.Label(setup, text="Participant ID (e.g., 001):").pack(pady=5)
    id_entry = tk.Entry(setup)
    id_entry.pack(pady=5)

    is_musician_var = tk.BooleanVar()
    tk.Checkbutton(setup, text="Is this participant a Jazz Musician?", variable=is_musician_var).pack(pady=10)

    def on_start():
        p_id = id_entry.get().strip()
        if not p_id:
            messagebox.showwarning("Input Error", "Please enter a Participant ID")
            return
        launch_experiment(p_id, is_musician_var.get(), setup)

    tk.Button(setup, text="Start Experiment", command=on_start, bg="blue", fg="white").pack(pady=20)
    setup.mainloop()

if __name__ == "__main__":
    show_setup_ui()