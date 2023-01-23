spaemis_glo: utilities.f90 spaemis_glo.f90
	gfortran -c -o utilities.o utilities.f90
	gfortran -o spaemis_glo spaemis_glo.f90 utilities.o

build: spaemis_glo

clean:
	rm -rf *.mod spaemis_glo