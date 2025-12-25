# Face Recognition Based Attendance System

A web-based attendance management system that uses face recognition technology to automatically mark attendance for students.

## Features

- **Face Recognition**: Uses OpenCV and face-recognition library to identify students
- **Student Registration**: Register students with their photos and details
- **Real-time Attendance**: Mark attendance in real-time using webcam
- **Faculty Dashboard**: Manage students, view attendance records
- **Student Portal**: Students can view their own attendance records
- **Download Reports**: Export attendance data to CSV files
- **Secure Authentication**: Separate login for faculty and students

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Computer Vision**: OpenCV, face-recognition
- **Frontend**: HTML, CSS, JavaScript
- **Session Management**: Flask-Session

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/face-recognition-attendance-system.git
   cd face-recognition-attendance-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and go to `http://localhost:5000`

## Usage

### For Faculty:
- Login with faculty credentials
- Register new students
- Start attendance session using webcam
- View and download attendance reports

### For Students:
- Login with roll number and password
- View personal attendance records

## Database Schema

- **students**: Stores student information and face encodings
- **faculty**: Stores faculty login credentials
- **attendance**: Records attendance with timestamps

## Security Notes

- Student passwords are hashed using Werkzeug
- Faculty passwords are stored in plain text (consider improving this)
- Session management for secure access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
