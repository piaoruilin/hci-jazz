# hci-jazz

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

If you install packages manually, do not repeat the word `install`:

```bash
python3 -m pip install mido fluidsynth pingouin seaborn matplotlib
```

For audio playback with `fluidsynth`, you may also need the FluidSynth system library on macOS:

```bash
brew install fluidsynth
```
