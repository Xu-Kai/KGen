FC := gfortran
FC_FLAGS :=

all : run

run : build
	./test.exe

build: test.exe

test.exe: test.o calling_module.o kernel.o module1.o module2.o types_mod.o types_mod1.o types_mod2.o
	${FC} -o $@ ${FC_FLAGS} $^

test.o: test_top.F90 calling_module.o
	${FC} -c -o $@ ${FC_FLAGS} $<

calling_module.o: calling_module.F90 kernel.o module1.o
	${FC} -c -o $@ ${FC_FLAGS} $<

kernel.o: kernel.F90 types_mod.o
	${FC} -c -o $@ ${FC_FLAGS} $<

module1.o: module1.F90 module2.o
	${FC} -c -o $@ ${FC_FLAGS} $<

module2.o: module2.F90 kernel.o
	${FC} -c -o $@ ${FC_FLAGS} $<

types_mod.o: types_mod.F90 types_mod1.o
	${FC} -c -o $@ ${FC_FLAGS} $<

types_mod1.o: types_mod1.F90 types_mod2.o
	${FC} -c -o $@ ${FC_FLAGS} $<

types_mod2.o: types_mod2.F90
	${FC} -c -o $@ ${FC_FLAGS} $<

clean:
	rm -f *.o *.exe *.mod
