# Mac Setup

## Installation

Ensure Apple's command line tools are installed.

    xcode-select --install

Ensure [Homebrew](https://brew.sh/) is installed.

    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Ensure [Ansible](http://docs.ansible.com/intro_installation.html) is installed.

    brew install ansible

Clone this repository to your local drive.

    git clone https://github.com/aptrik/mac-setup.git
    cd mac-setup
    ansible-playbook -vvv configure.yml
