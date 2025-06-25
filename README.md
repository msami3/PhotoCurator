# PhotoCurator

A FastAPI web app that organizes uploaded photos into meaningful folders using AI (CLIP model). It clusters photos semantically, identifies top picks by sharpness, and separates blurry images into a Trash folder.

---

## Prerequisites

- Python 3.9 or higher
- Pictures must be in **JPEG** format

---

## Setup & Run

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>


2. **Install required Python packages**

   ```bash
   pip3 install fastapi uvicorn transformers torch scikit-learn pillow opencv-python
   ```

3. **Install form data parser (required for file uploads)**

   ```bash
   pip3 install python-multipart
   ```

4. **Start the FastAPI server**

   ```bash
   python3 -m uvicorn photo_curator:app --reload
   ```

5. **Upload JPEG images via the `/organize` endpoint**

   * Use tools like Postman or your frontend to upload multiple JPEG files.
   * The app will process and organize them into output folders.

---

## Notes

* Only JPEG images are supported for input.
* The API endpoint for uploading files is `/organize`.
* Organized photos will be saved under the `organized_photos` folder by default.
* Make sure to have enough free disk space for output files.

---

## Example Usage with Postman

* POST to `http://127.0.0.1:8000/organize`
* Select form-data body type
* Use key `files` and upload multiple JPEG files

---
