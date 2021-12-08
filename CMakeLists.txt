project(dorie-wheel)
cmake_minimum_required(VERSION 3.16)

# Include the single source of versioning truth
include(dorie_version.cmake)

# Define a build rule clang-format
include(ExternalProject)

cmake_policy(SET CMP0074 NEW)

# Build hwloc - the version that OpenMPI bundles cannot be convinced to link
# statically against libxml2
ExternalProject_add(hwloc
  URL https://download.open-mpi.org/release/hwloc/v2.5/hwloc-2.5.0.tar.gz
  URL_HASH MD5=e9cb9230bcdf450b0948f255d505503f
  SOURCE_DIR ${CMAKE_BINARY_DIR}/hwloc
  CONFIGURE_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/hwloc ${CMAKE_COMMAND} -E env LDFLAGS=-static ./configure --enable-static --disable-shared --prefix=${CMAKE_BINARY_DIR}/hwloc-inst --disable-libxml2
  BUILD_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/hwloc ${CMAKE_COMMAND} -E env LDFLAGS=-all-static make
  INSTALL_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/hwloc make install
  INSTALL_DIR ${CMAKE_BINARY_DIR}/hwloc-inst
  BUILD_IN_SOURCE ON
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
)

# Build OpenMPI
ExternalProject_add(openmpi
  URL https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.0rc2.tar.gz
  URL_HASH MD5=9613d753f067a307933bdf9fd4231f21
  SOURCE_DIR ${CMAKE_BINARY_DIR}/openmpi
  CONFIGURE_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/openmpi ./configure --without-memory-manager --enable-static --disable-shared --prefix=${CMAKE_BINARY_DIR}/openmpi-inst --with-libevent=internal --with-hwloc=${CMAKE_BINARY_DIR}/hwloc-inst --with-pmix=internal --without-libnl --with-prrte=internal --disable-dlopen
  BUILD_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/openmpi make
  INSTALL_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/openmpi make install
  INSTALL_DIR ${CMAKE_BINARY_DIR}/openmpi-inst
  BUILD_IN_SOURCE ON
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
  DEPENDS hwloc
)

# Build HDF5
ExternalProject_add(hdf5
  URL https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.1/src/hdf5-1.12.1.tar.gz
  URL_HASH MD5=e4f057f0a3eb4237c7799605357a584d
  SOURCE_DIR ${CMAKE_BINARY_DIR}/hdf5
  CONFIGURE_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/hdf5 ${CMAKE_COMMAND} -E env CC=${CMAKE_BINARY_DIR}/openmpi-inst/bin/mpicc ./configure --enable-static --disable-shared --enable-parallel --prefix=${CMAKE_BINARY_DIR}/hdf5-inst
  INSTALL_COMMAND make install
  INSTALL_DIR ${CMAKE_BINARY_DIR}/hdf5-inst
  BUILD_IN_SOURCE ON
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
  DEPENDS openmpi
)

# Build FFTW3
ExternalProject_add(fftw3
  URL https://www.fftw.org/fftw-3.3.10.tar.gz
  URL_HASH MD5=8ccbf6a5ea78a16dbc3e1306e234cc5c
  SOURCE_DIR ${CMAKE_BINARY_DIR}/fftw3
  CONFIGURE_COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_BINARY_DIR}/fftw3 ${CMAKE_COMMAND} -E env CC=${CMAKE_BINARY_DIR}/openmpi-inst/bin/mpicc ./configure --enable-static --disable-shared --prefix=${CMAKE_BINARY_DIR}/fftw3-inst --enable-mpi
  INSTALL_COMMAND make install
  INSTALL_DIR ${CMAKE_BINARY_DIR}/fftw3-inst
  BUILD_IN_SOURCE ON
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
  DEPENDS openmpi
)

# CMAKE_ARGS
# -DBUILD_SHARED_LIBS:BOOL=OFF
# -DBUILD_TESTING:BOOL=OFF
# -DCMAKE_C_STANDARD=99
# -DCMAKE_FIND_PACKAGE_PREFER_CONFIG:BOOL=ON
# -DMPI_HOME=${CMAKE_BINARY_DIR}/openmpi-inst
# -DHDF5_ENABLE_PARALLEL:BOOL=ON
# -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/hdf5-inst
# )

# The CMake arguments that we pass to all Dune modules
set(DUNE_CMAKE_ARGS
  -DCMAKE_FIND_DEBUG_MODE=ON
  -DDUNE_PYTHON_INSTALL_LOCATION=none
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_EXE_LINKER_FLAGS=-static
  -DCMAKE_DISABLE_FIND_PACKAGE_TBB=ON
  -DSTDTHREAD_WORKS=ON
  -DMPI_HOME=${CMAKE_BINARY_DIR}/openmpi-inst
  -DCMAKE_PREFIX_PATH=${CMAKE_BINARY_DIR}/hdf5-inst
  -DCMAKE_DISABLE_FIND_PACKAGE_METIS=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_ParMETIS=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_PTScotch=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_PNG=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_GSL=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_ARPACK=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_ARPACKPP=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_SuperLU=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_SuiteSparse=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_LAPACK=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_BLAS=ON
  -DCMAKE_DISABLE_FIND_PACKAGE_GMP=ON
)

# Keep a list of Dune modules that we already build against. This replaces
# the logic of dependency tracking of Dune modules but requires us to add the
# Dune modules in a build-order-sorted fashion.
set(DUNE_MODULES)
set(DUNE_MODULES_DIRS)

# The function that implements the logic to add a Dune module via ExternalProject_add
function(add_dune_module)
  # Parse the given arguments
  cmake_parse_arguments(MODULE "" "NAME;URL;GITREV" "" ${ARGN})

  if(NOT MODULE_GITREV)
    set(MODULE_GITREV releases/2.6)
  endif()

  # Define an external project
  ExternalProject_add(${MODULE_NAME}
    GIT_REPOSITORY ${MODULE_URL}
    GIT_TAG ${MODULE_GITREV}
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${MODULE_NAME}
    BINARY_DIR ${CMAKE_BINARY_DIR}/build-${MODULE_NAME}
    UPDATE_COMMAND ""
    INSTALL_COMMAND ""
    USES_TERMINAL_DOWNLOAD 1
    USES_TERMINAL_CONFIGURE 1
    USES_TERMINAL_BUILD 1
    DEPENDS openmpi hdf5 fftw3 ${DUNE_MODULES}
    CMAKE_ARGS
      ${DUNE_MODULES_DIRS}
      ${DUNE_CMAKE_ARGS}
  )

  # Add this module to the list of modules
  set(DUNE_MODULES ${DUNE_MODULES} ${MODULE_NAME} PARENT_SCOPE)
  set(DUNE_MODULES_DIRS ${DUNE_MODULES_DIRS} -D${MODULE_NAME}_DIR=${CMAKE_BINARY_DIR}/build-${MODULE_NAME} PARENT_SCOPE)
endfunction()

# The sorted list of Dune modules that is required to build Dorie
add_dune_module(NAME dune-common URL https://gitlab.dune-project.org/core/dune-common)
add_dune_module(NAME dune-geometry URL https://gitlab.dune-project.org/core/dune-geometry)
add_dune_module(NAME dune-istl URL https://gitlab.dune-project.org/core/dune-istl)
add_dune_module(NAME dune-localfunctions URL https://gitlab.dune-project.org/core/dune-localfunctions)
add_dune_module(NAME dune-uggrid URL https://gitlab.dune-project.org/staging/dune-uggrid)
add_dune_module(NAME dune-grid URL https://gitlab.dune-project.org/core/dune-grid)
add_dune_module(NAME dune-typetree URL https://gitlab.dune-project.org/staging/dune-typetree)
add_dune_module(NAME dune-functions URL https://gitlab.dune-project.org/staging/dune-functions)
add_dune_module(NAME dune-pdelab URL https://gitlab.dune-project.org/pdelab/dune-pdelab)
add_dune_module(NAME dune-randomfield URL https://gitlab.dune-project.org/oklein/dune-randomfield)
add_dune_module(NAME dorie URL https://gitlab.dune-project.org/dorie/dorie GITREV v${DORIE_VERSION})

# Add patches to Dune modules - urgh
ExternalProject_Add_Step(
  dune-common dune-common-patch-1
  COMMAND git apply ${CMAKE_SOURCE_DIR}/patches/remove-tbb-call.patch
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/dune-common
  DEPENDEES download
)

ExternalProject_Add_Step(
  dorie dorie-patch-1
  COMMAND git apply ${CMAKE_SOURCE_DIR}/patches/disable-documentation.patch
#  COMMAND git apply ${CMAKE_SOURCE_DIR}/patches/randomfield-suggestion.patch
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/dorie
  DEPENDEES download
)

# Install the Dorie Python package into a location from which the Python sources
# for the pip-Python package are taken
install(
  DIRECTORY ${CMAKE_BINARY_DIR}/dorie/python/dorie
  DESTINATION pkg
)

# Keep a list of the Dorie executables
set(DORIE_EXECUTABLES
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d2_r0
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d2_r1
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d2_r2
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d2_r3
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d3_r0
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/richards_d3_r1
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d2_r0_t0
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d2_r1_t1
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d2_r2_t2
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d2_r3_t3
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d3_r0_t0
  ${CMAKE_BINARY_DIR}/build-dorie/dune/dorie/transport_d3_r1_t1
)

# Reduce the size of the executables using the strip tool
find_program(STRIP_EXECUTABLE strip)
if(STRIP_EXECUTABLE)
  add_custom_target(
    strip-dorie-executables
    ALL
    COMMAND ${STRIP_EXECUTABLE} ${DORIE_EXECUTABLES}
    COMMENT "Stripping Dorie executables for size reduction"
  )
  add_dependencies(strip-dorie-executables dorie)
endif()

# Install the Dorie executables
install(
  PROGRAMS ${DORIE_EXECUTABLES}
  DESTINATION pkg/dorie/cli
)
