update_zoekt:
    git submodule update --remote zoekt

build_zoekt_image:
    $(MAKE) update_zoekt
    cd zoekt && docker build -t zoekt-local:v0.0.1 .

build_spare_code_context_image:
    # Build the spare_code_context image
    cd spare_code_context && docker build -t spare_code_context:latest .
# index_data:
# 	STAGE=practice LANGUAGE=python docker compose up zoekt-indexer

# run_webserver:
# 	STAGE=practice LANGUAGE=python docker compose up zoekt-webserver