# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -I. # -I. includes the current directory for schema_generated.h
LDFLAGS =
LIBS = -lflatbuffers # Link against the FlatBuffers library

# --- Build Directory ---
# All output files will be placed here.
BUILD_DIR = build

# --- File names ---
# The target executable will be inside the build directory.
TARGET = $(BUILD_DIR)/client
SRCS = client.cpp
# Prepend the build directory path to the object file names.
OBJS = $(addprefix $(BUILD_DIR)/, $(SRCS:.cpp=.o))

# Default rule: builds the executable after ensuring the build directory exists.
all: $(BUILD_DIR) $(TARGET)

# Rule to create the build directory if it doesn't exist.
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# Rule to link the object files into the final executable.
$(TARGET): $(OBJS)
	$(CXX) $(LDFLAGS) -o $(TARGET) $(OBJS) $(LIBS)
	@echo "C++ client compiled successfully as '$(TARGET)'"

# Pattern rule to compile .cpp files into .o files inside the build directory.
$(BUILD_DIR)/%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Rule to run the client.
run: all
	@echo "--- Running C++ client ---"
	./$(TARGET)

# Rule to clean up the entire build directory.
clean:
	rm -rf $(BUILD_DIR)
	@echo "Cleaned up build directory."

# Phony targets are not actual files.
.PHONY: all clean run
