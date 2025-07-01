import os
import json
import uuid
import random
import time
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from cryptography.fernet import Fernet

# --- KHỞI TẠO ỨNG DỤNG VÀ CẤU HÌNH ---
# Đây là phần khởi tạo Flask và SocketIO.
app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

# --- MÃ HÓA (MÔ PHỎNG) ---
# Sử dụng thư viện cryptography để mô phỏng việc mã hóa dữ liệu.
# Trong thực tế, các thuật toán phức tạp hơn sẽ được sử dụng.
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_data(data_string):
    """Mã hóa một chuỗi sử dụng Fernet."""
    return cipher_suite.encrypt(data_string.encode('utf-8')).decode('utf-8')

# --- CẤU HÌNH LOGIN MANAGER ---
# Quản lý việc đăng nhập, đăng xuất và phiên làm việc của người dùng.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Vui lòng đăng nhập để truy cập."
login_manager.login_message_category = "info"

# --- LỚP USER VÀ CÁC HÀM HỖ TRỢ ---
# Định nghĩa cấu trúc của một người dùng và các hàm để đọc/ghi dữ liệu từ file JSON.
class User(UserMixin):
    def __init__(self, id, password, role, data={}):
        self.id = id
        self.password = password
        self.role = role
        self.data = data

USERS_DB = {}
USERS_FILE = 'users.json'

def load_users_from_file():
    """Tải danh sách người dùng từ tệp users.json."""
    global USERS_DB
    if not os.path.exists(USERS_FILE):
        # Nếu file không tồn tại, tạo dữ liệu mẫu
        initial_users = {
            "user_a": {"password": "123", "role": "client", "data": {"account_number": "111222333", "balance": 50000000, "pin": "1234", "pin_registered": True}},
            "user_b": {"password": "123", "role": "client", "data": {"account_number": "444555666", "balance": 25000000, "pin": "1234", "pin_registered": True}},
            "admin": {"password": "admin", "role": "admin", "data": {"score": 0}}
        }
        update_db_file(initial_users)
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        USERS_DB.clear()
        for username, userdata in data.items():
            # Đảm bảo các tài khoản cũ cũng có trường 'pin_registered'
            if userdata['role'] == 'client' and 'pin_registered' not in userdata.get('data', {}):
                userdata['data']['pin_registered'] = True # Mặc định là đã đăng ký cho tài khoản cũ
            USERS_DB[username] = User(username, userdata['password'], userdata['role'], userdata.get('data', {}))

def update_db_file(db_dict=None):
    """Cập nhật thay đổi vào tệp users.json."""
    source_db = db_dict if db_dict is not None else USERS_DB
    data_to_save = {}
    for username, user_obj in source_db.items():
        user_data = user_obj.data if isinstance(user_obj, User) else user_obj.get('data', {})
        data_to_save[username] = {
            'password': user_obj.password if isinstance(user_obj, User) else user_obj['password'], 
            'role': user_obj.role if isinstance(user_obj, User) else user_obj['role'],
            'data': user_data
        }
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)

@login_manager.user_loader
def load_user(user_id):
    """Hàm callback để Flask-Login tải thông tin người dùng."""
    return USERS_DB.get(user_id)

# --- CẤU HÌNH GAME ---
POINTS = {'correct': 25, 'wrong': -40}
TRANSACTION_REQUIREMENTS = {
    'balance_check': {'name': 'Yêu cầu Kiểm tra Số dư', 'sec': ['aes'], 'reason': 'Mã hóa AES là đủ để bảo vệ tính bí mật của thông tin số dư.'},
    'transfer': {'name': 'Yêu cầu Chuyển khoản', 'sec': ['aes', 'rsa', 'sha'], 'reason': 'Chuyển khoản cần bảo mật tối đa: AES (Bí mật), RSA (Chống giả mạo), và SHA (Toàn vẹn).'}
}
PENDING_TRANSFERS = {} # Lưu các giao dịch đang chờ OTP
ACTIVE_REQUESTS = {} # Lưu các yêu cầu đang chờ admin xử lý

# --- CÁC ROUTE (ĐIỀU HƯỚNG TRANG) ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'client':
            return redirect(url_for('banking_app'))
        else:
            return redirect(url_for('server_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        user = USERS_DB.get(request.form['username'])
        if user and user.role == 'client' and user.password == request.form['password']:
            login_user(user)
            # Nếu người dùng chưa đăng ký mã PIN, chuyển hướng đến trang đăng ký PIN
            if not user.data.get('pin_registered', False):
                flash('Chào mừng! Vui lòng thiết lập mã PIN bảo mật cho tài khoản của bạn.', 'info')
                return redirect(url_for('register_pin'))
            return redirect(url_for('banking_app'))
        flash('Sai tên đăng nhập hoặc mật khẩu.', 'error')
    return render_template('client_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        if username in USERS_DB:
            flash('Tên đăng nhập đã tồn tại.', 'error')
        else:
            # Khi đăng ký, mặc định chưa có PIN
            new_user = User(
                id=username, password=request.form['password'], role='client',
                data={
                    "account_number": str(random.randint(100000000, 999999999)), 
                    "balance": 10000000, 
                    "pin": None,
                    "pin_registered": False
                }
            )
            USERS_DB[username] = new_user
            update_db_file()
            client_accounts = [{'id': u.id, 'data': u.data} for u in USERS_DB.values() if u.role == 'client']
            socketio.emit('update_client_list', {'clients': client_accounts})
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
    return render_template('client_register.html')

@app.route('/register-pin', methods=['GET', 'POST'])
@login_required
def register_pin():
    # Nếu đã có PIN thì không cho vào trang này nữa
    if current_user.data.get('pin_registered', False):
        return redirect(url_for('banking_app'))

    if request.method == 'POST':
        pin = request.form.get('pin')
        confirm_pin = request.form.get('confirm_pin')

        if not pin or len(pin) != 4 or not pin.isdigit():
            flash('Mã PIN phải là 4 chữ số.', 'error')
            return render_template('register_pin.html')
        
        if pin != confirm_pin:
            flash('Mã PIN xác nhận không khớp.', 'error')
            return render_template('register_pin.html')

        # Lưu PIN và cập nhật trạng thái đã đăng ký
        user = USERS_DB[current_user.id]
        user.data['pin'] = pin
        user.data['pin_registered'] = True
        update_db_file()

        flash('Đăng ký mã PIN thành công!', 'success')
        return redirect(url_for('banking_app'))

    return render_template('register_pin.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        user = USERS_DB.get(request.form['username'])
        if user and user.role == 'admin' and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('server_dashboard'))
        flash('Sai thông tin đăng nhập hoặc bạn không phải Quản trị viên.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        if username in USERS_DB:
            flash('Tên admin đã tồn tại.', 'error')
        else:
            new_admin = User(id=username, password=request.form['password'], role='admin', data={"score": 0})
            USERS_DB[username] = new_admin
            update_db_file()
            flash('Tạo tài khoản admin thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

@app.route('/logout')
@login_required
def logout():
    role = current_user.role
    logout_user()
    return redirect(url_for('login' if role == 'client' else 'admin_login'))

@app.route('/server')
@login_required
def server_dashboard():
    if current_user.role != 'admin': return login_manager.unauthorized()
    client_accounts = [u for u in USERS_DB.values() if u.role == 'client']
    return render_template('server.html', clients=client_accounts)

@app.route('/app')
@login_required
def banking_app():
    if current_user.role != 'client': return login_manager.unauthorized()
    if not current_user.data.get('pin_registered', False):
        return redirect(url_for('register_pin'))
    recipients = [u for u in USERS_DB.values() if u.role == 'client' and u.id != current_user.id]
    return render_template('banking_app.html', recipients=recipients)

# --- LOGIC SOCKET.IO (TRÁI TIM CỦA ỨNG DỤNG) ---

@socketio.on('request_balance_check')
@login_required
def handle_balance_check_request(data):
    """Client yêu cầu xem số dư."""
    user = USERS_DB[current_user.id]
    balance = user.data.get('balance', 0)
    req_id = str(uuid.uuid4().hex)[:8]
    details = f"Người dùng {current_user.id} muốn xem số dư. Số dư hiện tại: {balance:,.0f} VND."
    
    request_data = {
        'id': req_id, 'user_id': current_user.id,
        'client_sid': request.sid, 'type_key': 'balance_check',
        'type_name': TRANSACTION_REQUIREMENTS['balance_check']['name'],
        'details': details
    }
    ACTIVE_REQUESTS[req_id] = {'data': request_data, 'admin_sid': None}
    emit('incoming_request', request_data, broadcast=True)

@socketio.on('request_transfer')
@login_required
def handle_transfer_request(data):
    """Client yêu cầu chuyển khoản."""
    recipient_id = data.get('recipient')
    if recipient_id not in USERS_DB or USERS_DB[recipient_id].role != 'client':
        emit('transfer_error', {'message': 'Người nhận không hợp lệ hoặc không tồn tại.'})
        return
    amount = float(data.get('amount', 0))
    if current_user.data['balance'] < amount:
        emit('transfer_error', {'message': 'Số dư không đủ.'})
        return
        
    req_id = str(uuid.uuid4().hex)[:8]
    details = f"Chuyển {amount:,.0f} VND từ {current_user.id} đến {recipient_id}."
    request_data = {
        'id': req_id, 'user_id': current_user.id,
        'client_sid': request.sid, 'type_key': 'transfer',
        'type_name': TRANSACTION_REQUIREMENTS['transfer']['name'],
        'details': details,
        'transfer_info': data
    }
    ACTIVE_REQUESTS[req_id] = {'data': request_data, 'admin_sid': None}
    emit('incoming_request', request_data, broadcast=True)

@socketio.on('request_security_action')
@login_required
def handle_security_action(data):
    """Admin tương tác với một hành động bảo mật (AES, RSA)."""
    if current_user.role != 'admin': return
    
    req_id = data.get('req_id')
    action = data.get('action')
    request_info = ACTIVE_REQUESTS.get(req_id)
    if not request_info: return

    # Gán admin xử lý yêu cầu này để các phản hồi sau chỉ gửi cho admin đó
    if not request_info['admin_sid']:
        request_info['admin_sid'] = request.sid

    if action == 'aes':
        details = request_info['data']['details']
        encrypted_details = encrypt_data(details)
        emit('security_action_result', {
            'req_id': req_id,
            'action': 'aes',
            'result': f"Mã hóa AES: {encrypted_details}"
        }, to=request.sid)

    elif action == 'rsa':
        client_sid = request_info['data']['client_sid']
        # Yêu cầu client nhập mã PIN
        emit('prompt_for_pin', {'req_id': req_id}, to=client_sid)
        # Báo cho admin biết là đang chờ
        emit('security_action_result', {
            'req_id': req_id,
            'action': 'rsa',
            'result': 'Đang chờ người dùng nhập mã PIN để ký...'
        }, to=request.sid)

@socketio.on('submit_pin')
@login_required
def handle_pin_submission(data):
    """Client gửi mã PIN để xác thực."""
    req_id = data.get('req_id')
    pin_submitted = data.get('pin')
    request_info = ACTIVE_REQUESTS.get(req_id)
    
    if not request_info or current_user.role != 'client': return

    admin_sid = request_info['admin_sid']
    correct_pin = current_user.data.get('pin')

    if pin_submitted == correct_pin:
        result_msg = "Xác thực PIN thành công! Chữ ký RSA hợp lệ."
        emit('pin_verification_result', {'req_id': req_id, 'success': True})
    else:
        result_msg = "Xác thực PIN thất bại! Chữ ký RSA không hợp lệ."
        emit('pin_verification_result', {'req_id': req_id, 'success': False})

    # Gửi kết quả xác thực PIN về cho admin đang xử lý
    if admin_sid:
        emit('security_action_result', {
            'req_id': req_id,
            'action': 'rsa',
            'result': result_msg
        }, to=admin_sid)

@socketio.on('secure_request')
@login_required
def handle_secure_request(data):
    """Admin nhấn nút cuối cùng để xử lý toàn bộ yêu cầu."""
    if current_user.role != 'admin': return
    
    req_id = data['id']
    req_type_key = data['type_key']
    actions_taken = data.get('actions', [])
    config = TRANSACTION_REQUIREMENTS[req_type_key]
    is_correct = set(actions_taken) == set(config['sec'])
    
    admin = USERS_DB[current_user.id]
    request_info = ACTIVE_REQUESTS.get(req_id)
    if not request_info: return

    client_sid = request_info['data']['client_sid']
    
    if is_correct:
        # Xử lý thành công
        if req_type_key == 'balance_check':
            admin.data['score'] += POINTS['correct']
            feedback = f"✅ CHÚC MỪNG: Xử lý chính xác! {config['reason']} (+{POINTS['correct']} điểm)."
            user = USERS_DB[request_info['data']['user_id']]
            emit('balance_check_approved', {'balance': user.data['balance']}, to=client_sid)
            emit('request_result', {'id': req_id, 'type_key': req_type_key, 'new_score': admin.data['score'], 'feedback': feedback, 'is_correct': True})
        
        elif req_type_key == 'transfer':
            otp = str(random.randint(100000, 999999))
            # Điểm sẽ được cộng/trừ sau khi client nhập OTP
            PENDING_TRANSFERS[req_id] = {
                'otp': otp, 
                'info': request_info['data']['transfer_info'], 
                'user_id': request_info['data']['user_id'], 
                'timestamp': time.time(),
                'admin_id': current_user.id, # Lưu lại admin đã xử lý
                'otp_attempts': 0
            }
            feedback = f"✅ Lựa chọn đúng. Đang chờ Client nhập mã OTP để hoàn tất giao dịch..."
            emit('otp_required', {'req_id': req_id, 'message': f"Mã OTP đã được gửi: {otp} (Mô phỏng)"}, to=client_sid)
            # Chỉ thông báo thành công bước 1, chưa cộng điểm
            emit('request_result', {'id': req_id, 'type_key': req_type_key, 'feedback': feedback, 'is_correct': True})

        update_db_file()
        if req_id in ACTIVE_REQUESTS:
            del ACTIVE_REQUESTS[req_id]

    else:
        # Nếu admin xử lý sai, yêu cầu sẽ được trả lại hàng chờ
        admin.data['score'] += POINTS['wrong']
        update_db_file()
        feedback = f"❌ LỰA CHỌN SAI bởi {current_user.id}. Yêu cầu được trả về hàng chờ. ({POINTS['wrong']} điểm)."
        request_info['admin_sid'] = None
        
        emit('request_requeued', {
            'id': req_id,
            'feedback': feedback,
            'new_score': admin.data['score'],
            'failed_admin_id': current_user.id
        }, broadcast=True)

        emit('processing_error_retrying', {
            'message': 'Lỗi xử lý phía server. Yêu cầu của bạn đang được xử lý lại. Vui lòng chờ...'
        }, to=client_sid)

@socketio.on('submit_otp')
@login_required
def handle_submit_otp(data):
    """Client gửi mã OTP để hoàn tất giao dịch, kèm theo logic cộng/trừ điểm."""
    req_id, otp = data.get('req_id'), data.get('otp')
    pending = PENDING_TRANSFERS.get(req_id)
    
    if not pending or (time.time() - pending['timestamp']) > 180: # Tăng thời gian chờ OTP
        emit('transfer_error', {'message': 'Mã OTP không hợp lệ hoặc đã hết hạn.'})
        if req_id in PENDING_TRANSFERS: del PENDING_TRANSFERS[req_id]
        return

    admin = USERS_DB.get(pending['admin_id'])

    if otp == pending['otp']:
        # --- OTP ĐÚNG ---
        sender_id, recipient_id, amount = pending['user_id'], pending['info']['recipient'], float(pending['info']['amount'])
        USERS_DB[sender_id].data['balance'] -= amount
        USERS_DB[recipient_id].data['balance'] += amount
        
        # Cộng điểm cho Admin
        admin.data['score'] += POINTS['correct']
        update_db_file()
        
        # Gửi biên lai cho Client
        receipt_data = {
            'time': datetime.now().strftime('%H:%M:%S %d/%m/%Y'), 'amount': f"{amount:,.0f} VND",
            'sender': sender_id, 'recipient': recipient_id, 'new_balance': USERS_DB[sender_id].data['balance']
        }
        emit('transfer_complete_receipt', receipt_data)
        
        # Cập nhật danh sách client cho mọi người
        client_accounts = [{'id': u.id, 'data': u.data} for u in USERS_DB.values() if u.role == 'client']
        socketio.emit('update_client_list', {'clients': client_accounts})
        
        # Thông báo thành công và cập nhật điểm cho Admin
        socketio.emit('otp_validation_complete', {
            'req_id': req_id,
            'admin_id': admin.id,
            'new_score': admin.data['score'],
            'success': True,
            'points_change': POINTS['correct'],
            'log_message': f"Giao dịch #{req_id} thành công! Client nhập đúng OTP."
        })

        del PENDING_TRANSFERS[req_id]
    else:
        # --- OTP SAI ---
        pending['otp_attempts'] += 1
        if pending['otp_attempts'] >= 3:
            # Trừ điểm của Admin
            admin.data['score'] += POINTS['wrong']
            update_db_file()
            
            # Hủy giao dịch và thông báo cho Client
            emit('transfer_error', {'message': f'Giao dịch #{req_id} đã bị hủy do nhập sai OTP quá 3 lần.'})
            
            # Thông báo thất bại và cập nhật điểm cho Admin
            socketio.emit('otp_validation_complete', {
                'req_id': req_id,
                'admin_id': admin.id,
                'new_score': admin.data['score'],
                'success': False,
                'points_change': POINTS['wrong'],
                'log_message': f"Giao dịch #{req_id} thất bại! Client nhập sai OTP 3 lần."
            })

            del PENDING_TRANSFERS[req_id]
        else:
            # Thông báo cho Client thử lại
            attempts_left = 3 - pending['otp_attempts']
            emit('otp_attempt_failed', {'message': f'OTP không chính xác. Bạn còn {attempts_left} lần thử.'})

# --- CHẠY ỨNG DỤNG ---
if __name__ == '__main__':
    load_users_from_file()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)