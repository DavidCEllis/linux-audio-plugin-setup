# Linux Audio Plugin Setup

This repository exists to guide in the setup and chaining of Windows VSTs on Linux using
[yabridge](https://github.com/robbert-vdh/yabridge) without locking your system to an old
version of Wine or even requiring a system WINE install.

It is expected that you know a little about how to use the terminal and how to install
packages from your distribution's package manager and flatpaks from flathub.

As a Fedora/Bazzite user these instructions are largely targeted at that distribution
family and will need to be modified if you use a Debian or Arch derived distro. I have
also tested this on Ubuntu 24.04 but not as thoroughly.

The final steps for stream setup also assume your distribution uses pipewire for audio
(try `pipewire --version` in a terminal)

The scripts provided place symlinks for configuration and applications to this folder to
make editing and updating the scripts or configuration files easier. This means this
folder needs to be in a specific place and should not be removed.

Note that this assumes you are using the standard `~/.local` and `~/.config` folders and
does not check XDG environment variables.

## Step 1 - Required Software

### Always Required

- This repository

  - Clone this repository into a directory you are not going to change
  - Some symlinks will be created to items in this folder so the scripts will break if you
    remove these files after setup

- [Bottles](https://flathub.org/en/apps/com.usebottles.bottles) - Wine environment manager

  - Install from the [flatpak](https://flathub.org/en/apps/com.usebottles.bottles)
  - `flatpak install flathub com.usebottles.bottles`

- [yabridge](https://github.com/robbert-vdh/yabridge) - Wrapper to make Windows VSTs work
  under Linux

  - Unfortunately this needs to be done manually at this point
  - Install using the Ubuntu/Debian/Mint instructions
    - Obtain the
      [yabridge-5.1.1.tar.gz](https://github.com/robbert-vdh/yabridge/releases/download/5.1.1/yabridge-5.1.1.tar.gz)
      archive from the [releases page](https://github.com/robbert-vdh/yabridge/releases)
    - Extract the contents of the downloaded archive to `~/.local/share`, such that the
      file `~/.local/share/yabridge/yabridgectl` exists after extracting.
    - Don't use the Fedora COPR for these instructions/scripts

- [yq](https://github.com/mikefarah/yq) - Command line YAML parser (used to get details
  from the wine environment)

  - Fedora: `sudo dnf install yq`
  - Fedora Atomic: `sudo rpm-ostree install yq` (reboot required)
  - Bazzite: `brew install yq`
  - Ubuntu: `sudo apt install yq`

- [python3-tkinter] - The usually included TK gui for Python scripts
  - For whatever reason this isn't included with bazzite by default, most other distros include it
  - Bazzite: `sudo rpm-ostree install python3-tkinter`

### Required only for streaming

- [Carla](https://kx.studio/Applications:Carla) - VST Host and audio routing
  - Carla's VST support is better and the routing is more flexible than using the VST
    filter included in OBS
  - Fedora: `sudo dnf install Carla`
  - Fedora Atomic/Bazzite: `sudo rpm-ostree install Carla` (case sensitive)
    - [The flatpak package will not work with the converted VSTs](https://github.com/robbert-vdh/yabridge?tab=readme-ov-file#tested-with)
    - The `brew` install under Bazzite failed to connect to JACK for some reason so was
      similarly unusable
    - There may be a way other than layering to get this to work, but I haven't had any
      luck
  - Ubuntu: `sudo apt install carla`

## Step 2 - Setting up the "Windows" environment and installing VSTs

In order for yabridge 5.1.1 to work you need a version of wine staging no later than
9.21[^1]. For this I'm using the 9.21-staging install from `Kron4ek` on the bottles
runners list.

In Bottles:

- Open preferences (ctrl+,)
- On the 'Runners' tab, open the 'Kron4ek' dropdown
- Install "kron4ek-wine-9.21-staging-tkg-amd64"
- Create a new bottle
  - I've usually used `Application` as the base, it may not be necessary
  - Reaplugs appear to work in a custom empty environment, but other plugins may need some
    extra dependencies
  - Make sure the Runner is "kron4ek-wine-9.21-staging-tkg-amd64" and not a different
    runtime
- Install your VSTs into this newly created bottle through the UI
  - I would install a small set to check everything works, you can install more later if
    needed

## Step 3 - Setting up YABridge

Some files need to be in place for yabridge to work correctly.

- Edit the runtime_config/wineloader.conf file `YABRIDGE_WINE` value if you have used a
  different install location or wine runtime

- Run `./setup_scripts/yabridge_setup.py` to install the configuration file and script

  - This will ask you to find 2 files to complete configuration
    - The first is the wine runner inside the 'kron4ek-wine-9.21-staging-tkg-amd64'
      directory, this should be in `bin/wine`
    - The second is the `bottle.yml` file for the default wine prefix you wish to use for
      yabridge
  - This will write a json file in a `user_config` folder in the folder with this readme
  - It will also create three symlinks
    - The wineloader.py script is linked into your `.local/bin` folder - this is the
      script that will be called instead of calling `wine` directly by tools that respect
      the `WINELOADER` environment variable
    - `wineloader.conf` is symlinked into `~/.config/environment.d` to set the
      `WINELOADER` environment variable to the path to `wineloader.py` automatically on
      login
    - `yabridgectl` is symlinked from the `~/.local/share` folder to `~/.local/bin` so it
      can be used directly

- **Reboot or logout and log back in to complete installation**

  - This will set the `WINELOADER` environment variable

- Run `./setup_scripts/yabridge_bottle_finder.py` to discover your VST folders

  - This will search for the standard VST folders within bottles and add the folders to
    yabridge

- Sync `yabridge` with your VSTs

  - run `yabridgectl sync`
  - You should see it list your new VSTs

## Extra Steps for setting up audio sinks for streaming

These steps are for setting up extra audio devices for streaming and are not necessary if
you are installing VSTs to use in a DAW.

### Step 4 - Setting up an Audio Sink (for streaming) (Requires pipewire)

This step adds a "desktop audio" device and a virtual "microphone" that can be used for
routing audio in Carla.

- Run `./setup_scripts/setup_pipewire_sinks.py`
  - If your system does not use pipewire, this should fail with an error message
  - If you had some applications using audio, this will disconnect them in order to add
    the new virtual devices

### Step 5 - Route your audio and setup your VSTs (for streaming)

Load up Carla and add your plugins.

- Check in Settings -> Plugin Paths that paths with `/home/USERNAME/.vst` and
  `/home/USERNAME/.vst3` are included
- Scan for VSTs
- You will have to work out which audio device represents your own hardware
  inputs/outputs.
- Use the patchbay to manage routing

After going through your effects chain, send the processed microphone to
`microphone-vst-sink` and desktop audio to `processed-audio-vst-sink`.

Routing

```
Desktop Audio -> VST Routing -> processed-audio-vst-sink
Microphone -> VST Routing -> microphone-vst-sink
```

### Step 6 - Connect OBS

- Launch OBS, set desktop audio to `Desktop Audio VST Processing Sink`, microphone to
  `Microphone VST Processing Sink`

## Sources

- Original yabridge wineloader script
  - https://github.com/microfortnight/yabridge-bottles-wineloader
  - The script included here modifies this by adding a fallback default WINE if there is no
    system WINE install
- Audio Sink Information
  - https://www.benashby.com/resources/pipewire-virtual-devices/
  - https://gitlab.freedesktop.org/pipewire/pipewire/-/wikis/Virtual-Devices#create-a-sink

[^1]: If you use a later version of Wine, your UI may not line up with your mouse cursor
due to changes in rendering.
