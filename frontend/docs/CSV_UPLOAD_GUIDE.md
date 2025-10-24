# CSV Upload Guide for Students

## Quick Start

Upload multiple students to a class at once using a CSV (Comma-Separated Values) file.

## CSV Format

### With Header Row

```csv
first_name,last_name,student_id,email
John,Doe,2024001,john.doe@example.com
Jane,Smith,2024002,jane.smith@example.com
Bob,Johnson,2024003,bob.johnson@example.com
Alice,Williams,2024004,alice.williams@example.com
```

**✅ Check** "CSV file has header row" option when uploading.

### Without Header Row

```csv
John,Doe,2024001,john.doe@example.com
Jane,Smith,2024002,jane.smith@example.com
Bob,Johnson,2024003,bob.johnson@example.com
Alice,Williams,2024004,alice.williams@example.com
```

**❌ Uncheck** "CSV file has header row" option when uploading.

## Required Fields

1. **First Name** (Column 1) - Student's first name
2. **Last Name** (Column 2) - Student's last name
3. **Student ID** (Column 3) - Unique identifier for the student

## Optional Fields

4. **Email** (Column 4) - Student's email address (can be empty)

## Examples

### Example 1: Students with Email

```csv
first_name,last_name,student_id,email
Michael,Brown,S2024001,michael.brown@university.edu
Sarah,Davis,S2024002,sarah.davis@university.edu
David,Miller,S2024003,david.miller@university.edu
```

### Example 2: Students without Email

```csv
first_name,last_name,student_id,email
Michael,Brown,S2024001,
Sarah,Davis,S2024002,
David,Miller,S2024003,
```

Or simply omit the email column if no header:

```csv
Michael,Brown,S2024001
Sarah,Davis,S2024002
David,Miller,S2024003
```

### Example 3: Large Class

```csv
first_name,last_name,student_id,email
Emma,Wilson,20240001,emma.w@school.edu
Liam,Anderson,20240002,liam.a@school.edu
Olivia,Taylor,20240003,olivia.t@school.edu
Noah,Thomas,20240004,noah.t@school.edu
Ava,Jackson,20240005,ava.j@school.edu
William,White,20240006,william.w@school.edu
Sophia,Harris,20240007,sophia.h@school.edu
James,Martin,20240008,james.m@school.edu
Isabella,Thompson,20240009,isabella.t@school.edu
Benjamin,Garcia,20240010,benjamin.g@school.edu
```

## How to Upload

### Step 1: Navigate to Class
Click on a class from the Classes page to open the Class Detail page.

### Step 2: Open Students Tab
Click on the "Students" tab (👥 Students).

### Step 3: Click Upload Button
Click the "📤 Upload CSV" button in the top-right corner.

### Step 4: Select File
1. Click "Choose File" or drag your CSV file
2. Select your CSV file from your computer
3. The filename will appear next to the button

### Step 5: Configure Header Option
- ✅ **Check** "CSV file has header row" if your first row contains column names
- ❌ **Uncheck** if your first row contains student data

### Step 6: Upload
Click the "Upload" button to start the import.

### Step 7: Review Results
The upload results will display:
- ✓ **Created**: Number of students successfully added
- ⚠ **Skipped**: Number of students that couldn't be added (with reasons)
- Detailed list of skipped entries

## Creating a CSV File

### Using Excel or Google Sheets

1. Create a spreadsheet with the following columns:
   ```
   | first_name | last_name | student_id | email |
   |------------|-----------|------------|-------|
   | John       | Doe       | 2024001    | ...   |
   ```

2. Fill in student data row by row

3. Export/Save as CSV:
   - **Excel**: File → Save As → Choose "CSV (Comma delimited)"
   - **Google Sheets**: File → Download → Comma-separated values (.csv)

### Using a Text Editor

1. Open Notepad, VS Code, or any text editor
2. Type student data with commas separating fields:
   ```
   first_name,last_name,student_id,email
   John,Doe,2024001,john@email.com
   Jane,Smith,2024002,jane@email.com
   ```
3. Save as `students.csv` (ensure extension is `.csv`, not `.txt`)

## Common Issues

### Issue: "Student ID already exists"

**Reason**: A student with that ID is already enrolled in the class.

**Solution**: 
- Check if the student already exists in the class
- Use a different student ID
- Remove duplicate from CSV

### Issue: "Missing required fields"

**Reason**: A row is missing first_name, last_name, or student_id.

**Solution**:
- Ensure all rows have at least 3 columns
- Check for empty cells in required columns
- Verify CSV format is correct

### Issue: "Invalid email format"

**Reason**: Email doesn't follow standard email format (user@domain.com).

**Solution**:
- Fix email format: `name@example.com`
- Leave email column empty if not available

### Issue: All students skipped

**Possible reasons**:
1. **Wrong header setting**: 
   - Try toggling the "has header row" checkbox
   
2. **Wrong CSV format**:
   - Ensure columns are comma-separated
   - Check file encoding (should be UTF-8)
   - Verify file extension is `.csv`

3. **All duplicates**:
   - Students already exist in the class
   - Check student IDs

## Best Practices

### 1. Test with Small File First
Upload a CSV with 2-3 students first to verify format.

### 2. Use Unique Student IDs
Ensure each student ID is unique within the class.

### 3. Clean Data Before Upload
- Remove extra spaces
- Check for typos
- Validate email formats

### 4. Keep Backup
Save your CSV file as backup in case you need to re-upload.

### 5. Use Consistent Format
Stick to one format (with/without headers) for all uploads.

## Column Order

**Important**: Columns must be in this exact order:

1. first_name
2. last_name  
3. student_id
4. email (optional)

❌ **Wrong order**:
```csv
student_id,first_name,last_name,email
2024001,John,Doe,john@email.com
```

✅ **Correct order**:
```csv
first_name,last_name,student_id,email
John,Doe,2024001,john@email.com
```

## Special Characters

### Allowed
- Letters (A-Z, a-z)
- Numbers (0-9)
- Hyphens (-)
- Underscores (_)
- Periods (.)
- @ symbol in emails

### Handle with Care
- **Commas**: Wrap field in quotes if it contains a comma
  ```csv
  first_name,last_name,student_id,email
  "Smith, Jr.",John,2024001,john@email.com
  ```
- **Quotes**: Escape with double quotes
  ```csv
  first_name,last_name,student_id,email
  John,O"Reilly,2024001,john@email.com
  ```

## File Size Limits

- **Recommended**: Up to 1,000 students per upload
- **Maximum**: 10 MB file size
- For very large classes (1,000+), consider splitting into multiple files

## Sample CSV Templates

### Template 1: Minimal (No Email)
```csv
first_name,last_name,student_id
John,Doe,2024001
Jane,Smith,2024002
Bob,Johnson,2024003
```

### Template 2: Complete (With Email)
```csv
first_name,last_name,student_id,email
John,Doe,2024001,john.doe@university.edu
Jane,Smith,2024002,jane.smith@university.edu
Bob,Johnson,2024003,bob.johnson@university.edu
```

### Template 3: Mixed (Some Emails)
```csv
first_name,last_name,student_id,email
John,Doe,2024001,john.doe@university.edu
Jane,Smith,2024002,
Bob,Johnson,2024003,bob.johnson@university.edu
```

## Download Sample Template

You can create your own template file:

1. Open text editor
2. Copy this content:
   ```csv
   first_name,last_name,student_id,email
   Student1_FirstName,Student1_LastName,ID001,student1@email.com
   Student2_FirstName,Student2_LastName,ID002,student2@email.com
   Student3_FirstName,Student3_LastName,ID003,student3@email.com
   ```
3. Replace example data with your students
4. Save as `my_students.csv`

## Troubleshooting

### CSV Won't Upload

1. **Check file extension**: Must be `.csv`, not `.txt` or `.xlsx`
2. **Check file size**: Must be under 10 MB
3. **Check format**: Open in text editor to verify comma separation
4. **Try different browser**: Some browsers handle file uploads differently

### Some Students Skipped

1. **Review skip reasons** in the upload results
2. **Fix issues** in the CSV file
3. **Re-upload** the corrected file
4. **Or add manually** using the "Add Student" button

### Need Help?

If you continue to have issues:
1. Check the detailed error messages in the upload results
2. Verify your CSV against the examples above
3. Try uploading a single student manually first
4. Contact system administrator if problem persists

---

**Tip**: Always review the upload results carefully to ensure all students were added correctly!
