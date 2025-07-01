# **Game_BaoMat_NganHang**

### *Học An Toàn Thông Tin Qua Trải Nghiệm Mô Phỏng Giao Dịch Ngân Hàng*

Một ứng dụng web tương tác được xây dựng bằng **Flask** và **Socket.IO**, game hóa quá trình học tập các nguyên tắc bảo mật cơ bản trong giao dịch: **Bí mật (Confidentiality)**, **Xác thực (Authentication)**, và **Toàn vẹn (Integrity)**.

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-v4-010101?style=for-the-badge&logo=socketdotio)
![Tailwind CSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)

-----

## 📝 Giới thiệu

Dự án này tạo ra một môi trường mô phỏng thời gian thực, nơi người dùng có thể đóng hai vai trò:

1.  **👤 Client (Người dùng Ngân hàng):** Thực hiện các giao dịch cơ bản như xem số dư và chuyển khoản.
2.  **🛡️ Admin (Chuyên viên Trung tâm Điều hành An ninh - SOC):** Theo dõi các yêu cầu giao dịch đến và áp dụng đúng các biện pháp bảo mật (Mã hóa **AES**, Ký số **RSA**, Băm **SHA**) để xử lý chúng.

Mục tiêu của người chơi Admin là đưa ra quyết định chính xác để bảo vệ hệ thống, hoàn thành giao dịch cho người dùng và ghi điểm. Mỗi quyết định sai lầm sẽ bị trừ điểm và có thể ảnh hưởng đến luồng giao dịch.

## ✨ Tính năng nổi bật

  * **⚡ Tương tác thời gian thực:** Sử dụng **Flask-SocketIO** để tạo ra trải nghiệm đa người dùng mượt mà, nơi hành động của người này ảnh hưởng ngay lập tức đến người khác.
  * **🎭 Hệ thống hai vai trò:** Tách biệt rõ ràng giữa người dùng cuối (Client) và người vận hành hệ thống (Admin) với giao diện được thiết kế riêng.
  * **🖥️ Giao diện SOC chuyên nghiệp:** Bảng điều khiển dành cho Admin được thiết kế với nền tối, hiển thị hàng chờ yêu cầu, nhật ký hệ thống và các thông tin quan trọng khác.
  * **🧩 Mô phỏng các giao thức bảo mật:**
      * **Bí mật (AES):** Mô phỏng mã hóa đối xứng để bảo vệ thông tin.
      * **Xác thực (RSA):** Mô phỏng chữ ký số và xác thực thông qua cơ chế mã PIN.
      * **Toàn vẹn (SHA):** Mô phỏng việc kiểm tra tính toàn vẹn của dữ liệu.
  * **🎮 Yếu tố Gamification:** Hệ thống tính điểm, thưởng phạt và phản hồi tức thì để tạo động lực và nâng cao hiệu quả học tập.
* **🎨 Giao diện hiện đại:** Giao diện người dùng được xây dựng với **Tailwind CSS**, đảm bảo tính thẩm mỹ và đáp ứng tốt trên các thiết bị.

## 🚀 Demo & Hình ảnh

*(GỢI Ý: Bạn có thể đăng tải ứng dụng lên một dịch vụ miễn phí như PythonAnywhere, Heroku và dán link vào đây)*
**Link Demo:** `[Chưa có]`

*(GỢI Ý: Thay thế các link `https://placehold.co/...` bằng link ảnh chụp màn hình thực tế của bạn đã được tải lên GitHub hoặc một dịch vụ host ảnh)*

| Giao diện Client (Ngân hàng) | Giao diện Admin (SOC) |
| :-------------------------: | :-----------------------: |
| ![Giao diện Client](https://placehold.co/600x400/f1f5f9/0f172a?text=Giao+diện+Client) | ![Giao diện Admin](https://placehold.co/600x400/0f172a/e2e8f0?text=Giao+diện+Admin) |
| **Thẻ Yêu cầu Tương tác** | **Luồng Giao dịch Hoàn chỉnh** |
| ![Thẻ yêu cầu](https://placehold.co/600x400/0f172a/e2e8f0?text=Thẻ+Yêu+cầu) | ![Luồng giao dịch](https://placehold.co/600x400/f1f5f9/0f172a?text=Luồng+Giao+dịch) |

## 🛠️ Công nghệ sử dụng

  * **Backend:**
      * Python 3
      * Flask
      * Flask-SocketIO
      * Flask-Login
      * Cryptography
  * **Frontend:**
      * HTML5
      * Tailwind CSS
      * JavaScript
      * Socket.IO Client
  * **Cơ sở dữ liệu:**
      * Tệp JSON (sử dụng cho mục đích mô phỏng)

## ⚙️ Cài đặt & Chạy dự án

### Yêu cầu

  * Python (phiên bản 3.6 trở lên)
  * `pip` và `venv`

### Các bước cài đặt

1.  **Clone repository về máy của bạn:**

    ```bash
    git clone [URL-repository-cua-ban]
    cd [ten-repository-cua-ban]
    ```

2.  **Tạo và kích hoạt môi trường ảo:**

    ```bash
    # Tạo môi trường ảo
    python -m venv venv

    # Kích hoạt trên Windows
    .\venv\Scripts\activate

    # Kích hoạt trên macOS/Linux
    source venv/bin/activate
    ```

3.  **Tạo tệp `requirements.txt`:**
    Tạo một tệp mới tên là `requirements.txt` trong thư mục gốc và dán nội dung sau vào:

    ```
    Flask
    Flask-SocketIO
    Flask-Login
    cryptography
    ```

4.  **Cài đặt các thư viện cần thiết:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Chạy ứng dụng:**

    ```bash
    python app.py
    ```

6.  **Truy cập ứng dụng:**

      * **Client:** Mở trình duyệt và truy cập `http://127.0.0.1:5000`
      * **Admin:** Mở một cửa sổ trình duyệt khác (hoặc cửa sổ ẩn danh) và truy cập `http://127.0.0.1:5000/admin/login`

## 📂 Cấu trúc dự án

/
|-- app.py              # Logic chính của server
|-- users.json          # Database giả lập
|-- requirements.txt    # Danh sách các thư viện Python
|-- README.md           # Tệp bạn đang đọc
|
|-- /templates
|-- layout.html
|-- banking_app.html
|-- server.html
|-- admin_login.html
|-- admin_register.html
|-- client_login.html
|-- client_register.html
|-- client_pin.html
