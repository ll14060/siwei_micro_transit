# Getting Started with Siwei Micro Transit

Welcome! To set up the project correctly with all submodules and large data folders, please follow these steps carefully.

## 1. Clone the repository with submodules

Run this command to clone the main repo and initialize all submodules:

```bash
git clone --recurse-submodules https://github.com/ll14060/siwei_micro_transit/
```
2. Download and place large data files manually

Because some files are too large to track via Git, please download and place them as follows:

    Place the Data folder inside the main repo folder.

    Place the Road Network Data folder inside Ritun/Latest network/

    Place the SCAG folder inside Ritun/Latest network 2/

3. Configure Git to handle submodule pushes automatically

Run this command once to enable automatic submodule pushes and pulls:

``` git config --global push.recurseSubmodules on-demand ```

4. Work normally with Git commands

After this setup, you can work as usual with:

    git pull to fetch updates (including submodules)

    git commit to save changes

    git push to push changes (including submodules)

If you run into any issues or need help, feel free to ask!
