# Installing Plex Meta Manager

## Install Walkthroughs

These installation overviews are aimed at users who have previous experience of installing services via command-line terminal commands. For those who need full installation walkthroughs, please refer to the following walkthrough guides:

  * [Local Walkthrough](guides/local)
  * [Docker Walkthrough](guides/docker)
  * [unRAID Walkthrough](guides/unraid)
  * [Kubernetes Walkthrough](guides/kubernetes)

## Local Install Overview

Plex Meta Manager is compatible with Python 3.7, 3.8 or 3.9 only. Later versions may function but are untested.

These are high-level steps which assume the user has knowledge of python and pip, and the general ability to troubleshoot issues. For a detailed step-by-step walkthrough, refer to the [Local Walkthrough](guides/local) guide.

1. Clone or [download and unzip](https://github.com/meisnate12/Plex-Meta-Manager/archive/refs/heads/master.zip) the repo.

```shell
git clone https://github.com/meisnate12/Plex-Meta-Manager
```
2. Install dependencies:

```shell
pip install -r requirements.txt
```

3. If the above command fails, run the following command:

```shell
pip install -r requirements.txt --ignore-installed
```

At this point Plex Meta Manager has been installed, and you can verify installation by running:

```shell
python plex_meta_manager.py
```

## Docker Install Overview

### Docker Run:

```shell
docker run -it -v <PATH_TO_CONFIG>:/config:rw meisnate12/plex-meta-manager
```
* The `-it` flag allows you to interact with the script when needed (such as for Trakt or MyAnimeList authentication).
* The `-v <PATH_TO_CONFIG>:/config:rw` flag mounts the location you choose as a persistent volume to store your files.
  * Change `<PATH_TO_CONFIG>` to a folder where your config.yml and other files are.
  * The docker image defaults to running the configuration file named `config.yml` which resides in your persistent volume.
  * If your directory has spaces (such as "My Documents"), place quotation marks around your directory pathing as shown here: `-v "<PATH_TO_CONFIG>:/config:rw"`


Example Docker Run command:

These docs are assuming you have a basic understanding of Docker concepts.  One place to get familiar with Docker would be the [official tutorial](https://www.docker.com/101-tutorial/).

```shell
docker run -it -v "X:\Media\Plex Meta Manager\config:/config:rw" meisnate12/plex-meta-manager
```

### Docker Compose:

Example Docker Compose file:
```yaml
version: "2.1"
services:
  plex-meta-manager:
    image: meisnate12/plex-meta-manager
    container_name: plex-meta-manager
    environment:
      - TZ=TIMEZONE #optional
    volumes:
      - /path/to/config:/config
    restart: unless-stopped
```
## Dockerfile
A `Dockerfile` is included within the GitHub repository for those who require it, although this is only suggested for those with knowledge of dockerfiles. The official Plex Meta Manager build is  available on the [Dockerhub Website](https://hub.docker.com/r/meisnate12/plex-meta-manager).