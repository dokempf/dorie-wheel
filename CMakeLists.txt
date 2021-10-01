project(dorie-wheel)
cmake_minimum_required(VERSION 3.16)

# Include the single source of versioning truth
include(dorie_version.cmake)

# Define a build rule clang-format
include(ExternalProject)

# Build FakeMPI
ExternalProject_add(fakempi
  GIT_REPOSITORY https://github.com/dokempf/FakeMPI
  GIT_TAG experimental-additions
  SOURCE_DIR ${CMAKE_BINARY_DIR}/fakempi
  BINARY_DIR ${CMAKE_BINARY_DIR}/build-fakempi
  INSTALL_DIR ${CMAKE_BINARY_DIR}/install-fakempi
  UPDATE_COMMAND ""
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
  CMAKE_ARGS
    -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/install-fakempi
    -DBUILD_SHARED_LIBS:BOOL=OFF
)


# Build HDF5 - wild
# https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report.pdf
ExternalProject_add(hdf5
  GIT_REPOSITORY https://github.com/HDFGroup/hdf5
  GIT_TAG hdf5-1_12_1
  SOURCE_DIR ${CMAKE_BINARY_DIR}/hdf5
  BINARY_DIR ${CMAKE_BINARY_DIR}/build-hdf5
  UPDATE_COMMAND ""
  INSTALL_COMMAND ""
  USES_TERMINAL_DOWNLOAD 1
  USES_TERMINAL_CONFIGURE 1
  USES_TERMINAL_BUILD 1
  DEPENDS fakempi
  CMAKE_ARGS
    -DBUILD_SHARED_LIBS:BOOL=OFF
    -DBUILD_TESTING:BOOL=OFF
    -DCMAKE_C_FLAGS="-DMPI_FILE_NULL=1"
    -DCMAKE_FIND_PACKAGE_PREFER_CONFIG:BOOL=ON
    -DCMAKE_PREFIX_PATH=${CMAKE_BINARY_DIR}/install-fakempi
    -DHDF5_ENABLE_PARALLEL:BOOL=ON
)

# Skip the rest for now
return()

# The CMake arguments that we pass to all Dune modules
set(DUNE_CMAKE_ARGS 
  -DDUNE_PYTHON_INSTALL_LOCATION=none
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_EXE_LINKER_FLAGS=-static
  -DCMAKE_DISABLE_FIND_PACKAGE_TBB=ON
  -DSTDTHREAD_WORKS=ON
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

  # Form a string for dependencies
  set(DEPENDS_OPT "")
  if(DUNE_MODULES)
    set(DEPENDS_OPT DEPENDS ${DUNE_MODULES})
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
    ${DEPENDS_OPT}
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
#add_dune_module(NAME dune-randomfield URL https://gitlab.dune-project.org/oklein/dune-randomfield)
add_dune_module(NAME dorie URL https://ts-gitlab.iup.uni-heidelberg.de/dorie/dorie GITREV v${DORIE_VERSION})

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
  COMMAND git apply ${CMAKE_SOURCE_DIR}/patches/randomfield-suggestion.patch
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
