# Spare Code Context

Official implementation of the "SpareCodeSearch: How to *search* for *code* context when you do not have a *spare* GPU" - submitted at the [ASE 2025 Context Collection Workshop](https://jetbrains-research.github.io/ase2025-context-collection-workshop/).

This solution also won the golden price in [Kotlin track](https://lp.jetbrains.com/research/context-collection-competition/?tab-1756138596455-4232=kotlin) 🥇 and the silver price in [Python track](https://lp.jetbrains.com/research/context-collection-competition/?tab-1756138596455-4232=python) 🥈 of the corresponding Context Collection Competition organized by Jetbrains and Mistral AI.

## Prepare Data
The structure for data is kept in accordance with the original competition data structure, which is as follows:
```bash
data
├── {language}-{stage}.jsonl # Competition data
└── repositories-{language}-{stage} # Folder with repositories
    └── {owner}__{repository}-{revision} # Repository revision used for collecting context
        └── repository contents
```

To prepare data for the starter kit:
1. Download the data for the respective stage from [the shared folder](https://drive.google.com/drive/folders/1wcpq7ob33z5wHNFzUaiJWuHWw8sNuumC). Please note: unpacked data takes ~10GB on disk.
2. Put the `{language}-{stage}.jsonl` file (datapoints) and the `{language}-{stage}.zip` archive (repos) to the `data` folder.
3. Run `./prepare_data.sh practice python`, possibly replacing `practice` with the stage and `python` with `kotlin`.

## Build and Run Spare Code Context
### Clone the repository and its submodules (Zoekt)

```bash
git clone --recurse-submodules https://github.com/minhna1112/spare-code-search.git
git submodule update --remote zoekt
```
### Build the Zoekt Code Search Server Docker images on local machine
```bash
 cd zoekt && docker build -t zoekt-local:v0.0.1 . && docker tag zoekt-local:v0.0.1 zoekt-local:latest
```
### Step 1: Index the data
To index the data, you need to run the `zoekt-indexer` service. This service will read the data from the `data` folder and index it for searching. 
```bash
STAGE=public LANGUAGE=kotlin docker-compose up zoekt-indexer
```
### Step 2: Start the Zoekt web server
The Indexing process will take some time, depending on the size of the data and your machine's performance. Once the indexing is complete, you can start the `zoekt-webserver` service to provide a search interface.
```bash
STAGE=public LANGUAGE=kotlin docker-compose up zoekt-webserver
```
### Step 3: Build and run the Spare Code Context Docker image
Everything is set up, and you can now build and run the Spare Code Context Docker image. Everytime you want to run the Spare Code Context, you need to run the following command:
```bash
docker-compose up spare-code-context --build --force-recreate
```
You can modify the `docker-compose.yml` file to set the appropriate environment variables for your `STAGE` and `LANGUAGE`. All other volumes and environment variables are set in the `docker-compose.yml` file.
```yml
environment:
    - STAGE=${STAGE:-public}  # Default to 'public' stage if not set
    - LANGUAGE=${LANGUAGE:-kotlin}  # Default to 'kotlin' language if not set
    - ZOEKT_URL=http://zoekt-webserver:6070/api/search  # URL of the zoekt web server
```
The `ZOEKT_URL` is the URL of the Zoekt web server that provides the search API, which should be left as is unless you have a custom setup.
All the volumes are mounted to the `spare_code_context` container
```yml
volumes:
    - ./data:/data  # Mount local data directory
    - ./predictions:/predictions  # Mount local predictions directory
    - ./queries:/queries  # Mount local queries directory
```
After every run, you can find the predictions in the `predictions` folder, which will be created if it does not exist. The predictions will be saved in the format `{language}-{stage}-predictions.jsonl`, where `language` and `stage` are the same as in the `docker-compose.yml` file.
