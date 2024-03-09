# clone the HiGHS repository
git clone https://github.com/ERGO-Code/HiGHS.git

# change into the highs direcory
cd HiGHS

# build the highs library
cmake -S . -B build
cmake --build build
cmake --install build

# revert back to the original directory
cd ..
