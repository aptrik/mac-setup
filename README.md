# Mac Setup

## Prerequisites

Ensure Apple's command line tools are installed.

    xcode-select --install

Install Rosetta

    softwareupdate --install-rosetta --agree-to-license

Ensure [Homebrew](https://brew.sh/) is installed.

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Ensure [Ansible](http://docs.ansible.com/intro_installation.html) is installed.

    brew install ansible
    ansible-galaxy collection install community.general

Upgrade the collection to the latest version:

    ansible-galaxy collection install community.general --upgrade

## Collecting Current Settings

Export your current macOS settings (Dock layout, Finder preferences, keyboard
repeat rates, etc.) to `settings.yml`:

    ./scripts/collect.py

This reads preferences from `~/Library/Preferences/` and saves them in a
portable YAML format. Commit `settings.yml` to the repository so it can be
used to restore settings on a new machine.

## Applying Configuration

Dry-run (check mode — no changes are made):

    ansible-playbook --check configure.yml

Apply the full configuration:

    ansible-playbook configure.yml

Or pull and apply directly from the repository:

    ansible-pull --only-if-changed --url https://github.com/aptrik/mac-setup.git configure.yml

The playbook will:

1. Install Homebrew packages and casks.
2. Apply macOS settings from `settings.yml` (Dock, Finder, Keyboard) if present.
3. Sync Dock items (apps and folders) to match `settings.yml`.

## TODO

### Software Update

#### Ignore Specific Software Update

The identifier can be found via softwareupdate --list. In the example below, being on Mojave, will ignore all update prompts to Catalina, since the latter removes 32-bit support.

    sudo /usr/sbin/softwareupdate --ignore "macOS Catalina"

#### Show Available Software Updates

    sudo softwareupdate --list

#### Install All Available Software Updates

    sudo softwareupdate -ia


#### Disable Gatekeeper

    sudo spctl --master-disable

### Bash

Install the latest version and set as current user's default shell:

    brew install bash && \
        echo $(brew --prefix)/bin/bash | sudo tee -a /etc/shells && \
        chsh -s $(brew --prefix)/bin/bash

### Mail

Show Attachments as Icons

    defaults write com.apple.mail DisableInlineAttachmentViewing -bool yes

### Dock

Add a Stack with Recent Applications

    defaults write com.apple.dock persistent-others -array-add '{ "tile-data" = { "list-type" = 1; }; "tile-type" = "recents-tile"; }' && \
        killall Dock

Autohide

    # Enable
    defaults write com.apple.dock autohide -bool true && \
        killall Dock

### Finder

Show All File Extensions

    defaults write -g AppleShowAllExtensions -bool true

Show Path Bar

    defaults write com.apple.finder ShowPathbar -bool true

### Keyboard

Full Keyboard Access

    # All controls
    defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

Key Repeat Rate

    defaults read -g KeyRepeat
    defaults read -g InitialKeyRepeat

    defaults write -g InitialKeyRepeat -int 12   # 180ms (default minimum is 15 == 225ms)
    defaults write -g KeyRepeat -int 1           #  15ms (default minimum is 2 == 30ms)

### Hostname

Set Computer Name/Host Name

    newhostname=XYZ
    sudo scutil --set ComputerName "$newhostname" && \
    sudo scutil --set HostName "$newhostname" && \
    sudo scutil --set LocalHostName "$newhostname" && \
    sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string "$newhostname"

### Login Window

Set Login Window Text

    sudo defaults write /Library/Preferences/com.apple.loginwindow LoginwindowText "Your text"
