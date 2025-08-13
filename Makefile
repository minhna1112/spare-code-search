update_zoekt:
	git submodule update --remote zoekt

build_zoekt_image:
	cd zoekt && docker build -t zoekt-local:v0.0.1 .