TARGET = 4700ftp
PYTHON_SCRIPT = 4700ftp.py

# Submission Archive
SUBMISSION_ZIP = 4700ftp_submission.zip

.PHONY: all clean run package

# Default target
all:
	@chmod +x $(PYTHON_SCRIPT)
	@ln -sf $(PYTHON_SCRIPT) $(TARGET)

# Run the script
run:
	@./$(TARGET) --help

# Create a ZIP file for submission
package:
	@zip -r $(SUBMISSION_ZIP) $(PYTHON_SCRIPT) Makefile README.md

clean:
	@rm -f $(TARGET) $(SUBMISSION_ZIP)
