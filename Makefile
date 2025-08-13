update_zoekt:
    git submodule update --remote zoekt

build_zoekt_image:
    # Ensure the zoekt submodule is updated before building the image
    $(MAKE) update_zoekt
    cd zoekt && docker build -t zoekt-local:v0.0.1 .

index_data:
	STAGE=practice LANGUAGE=python docker compose up zoekt-indexer

run_webserver:
	STAGE=practice LANGUAGE=python docker compose up zoekt-webserver