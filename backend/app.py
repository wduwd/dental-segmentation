from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_cors import CORS
import os
from datetime import datetime
#修改过的代码
app = Flask(__name__)

# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dorm_repair.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'

# 创建上传文件夹
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化扩展
CORS(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, repairman, admin
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))

class RepairOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    repairman_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    appointment_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, repairing, completed, rejected
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = db.Column(db.DateTime)
    student = db.relationship('User', foreign_keys=[student_id], backref='student_orders')
    repairman = db.relationship('User', foreign_keys=[repairman_id], backref='repairman_orders')
    category = db.relationship('Category', backref='repair_orders')

class RepairImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_order_id = db.Column(db.Integer, db.ForeignKey('repair_order.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    repair_order = db.relationship('RepairOrder', backref='images')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_order_id = db.Column(db.Integer, db.ForeignKey('repair_order.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    repair_order = db.relationship('RepairOrder', backref='comment')
    student = db.relationship('User', backref='comments')

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    author = db.relationship('User', backref='announcements')

# 创建数据库表
with app.app_context():
    db.create_all()
    # 添加默认用户
    from werkzeug.security import generate_password_hash
    
    # 管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('123456'),
            name='系统管理员',
            role='admin',
            phone='13800138000',
            email='admin@example.com'
        )
        db.session.add(admin)
    
    # 学生用户
    student = User.query.filter_by(username='20210001').first()
    if not student:
        student = User(
            username='20210001',
            password=generate_password_hash('123456'),
            name='张三',
            role='student',
            phone='13800138001',
            email='student@example.com'
        )
        db.session.add(student)
    
    # 维修人员用户
    repairman = User.query.filter_by(username='repair001').first()
    if not repairman:
        repairman = User(
            username='repair001',
            password=generate_password_hash('123456'),
            name='李师傅',
            role='repairman',
            phone='13800138002',
            email='repairman@example.com'
        )
        db.session.add(repairman)
    
    db.session.commit()
    # 添加默认故障分类
    categories = ['水电', '家具', '门窗', '网络', '其他']
    for name in categories:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name)
            db.session.add(cat)
    db.session.commit()

# 认证相关API
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    
    from werkzeug.security import check_password_hash
    if not check_password_hash(user.password, password):
        return jsonify({'code': 401, 'msg': '密码错误'})
    
    # 创建JWT Token
    access_token = create_access_token(identity=str(user.id))
    
    # 返回用户信息和Token
    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'data': {
            'token': access_token,
            'userInfo': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'phone': user.phone,
                'email': user.email,
                'avatar': user.avatar
            }
        }
    })

# 获取当前用户信息
@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    
    return jsonify({
        'code': 200,
        'msg': '获取成功',
        'data': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'phone': user.phone,
            'email': user.email,
            'avatar': user.avatar
        }
    })

# 修改密码
@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    from werkzeug.security import check_password_hash, generate_password_hash
    if not check_password_hash(user.password, current_password):
        return jsonify({'code': 401, 'msg': '原密码错误'})
    
    user.password = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '密码修改成功'})

# 更新个人信息
@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    data = request.json
    
    # 更新用户信息（不允许更新角色）
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    try:
        db.session.commit()
        return jsonify({
            'code': 200,
            'msg': '个人信息更新成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'phone': user.phone,
                'email': user.email,
                'avatar': user.avatar
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '更新失败', 'error': str(e)})

# 报修相关API
@app.route('/api/repairs', methods=['POST'])
@jwt_required()
def create_repair_order():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'student':
        return jsonify({'code': 403, 'msg': '只有学生可以提交报修'})
    
    data = request.json
    category_id = data.get('category')
    room = data.get('room')
    description = data.get('description')
    appointment_time = data.get('appointment_time')
    images = data.get('images', [])
    
    # 验证必填字段
    if not all([category_id, room, description]):
        return jsonify({'code': 400, 'msg': '请填写完整的报修信息'})
    
    try:
        # 转换预约时间
        if appointment_time:
            appointment_time = datetime.strptime(appointment_time, '%Y-%m-%d %H:%M')
        
        # 创建报修单
        repair_order = RepairOrder(
            student_id=current_user_id,
            category_id=category_id,
            room=room,
            description=description,
            appointment_time=appointment_time,
            status='pending'
        )
        db.session.add(repair_order)
        db.session.flush()  # 获取repair_order.id
        
        # 保存图片信息
        for image_path in images:
            repair_image = RepairImage(
                repair_order_id=repair_order.id,
                image_path=image_path
            )
            db.session.add(repair_image)
        
        db.session.commit()
        
        return jsonify({'code': 200, 'msg': '报修提交成功', 'data': {'repair_order_id': repair_order.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '提交失败', 'error': str(e)})

# 获取用户的报修单列表
@app.route('/api/repairs', methods=['GET'])
@jwt_required()
def get_repair_orders():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role == 'student':
        orders = RepairOrder.query.filter_by(student_id=current_user_id).all()
    elif user.role == 'repairman':
        orders = RepairOrder.query.filter_by(repairman_id=current_user_id).all()
    else:  # admin
        orders = RepairOrder.query.all()
    
    result = []
    for order in orders:
        result.append({
            'id': order.id,
            'room': order.room,
            'description': order.description,
            'category': order.category.name if order.category else '',
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'student_name': order.student.name if order.student else '',
            'repairman_name': order.repairman.name if order.repairman else '',
            'images': [img.image_path for img in order.images]
        })
    
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

# 获取单个报修单详情
@app.route('/api/repairs/<int:order_id>', methods=['GET'])
@jwt_required()
def get_repair_order_detail(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 获取报修单
    order = RepairOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    # 检查权限：学生只能查看自己的报修单，管理员和维修人员可以查看所有
    if user.role == 'student' and order.student_id != current_user_id:
        return jsonify({'code': 403, 'msg': '无权查看该报修单'})
    
    # 获取评论
    comment = Comment.query.filter_by(repair_order_id=order_id).first()
    comment_info = None
    if comment:
        comment_info = {
            'id': comment.id,
            'rating': comment.rating,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # 构建响应数据
    result = {
        'id': order.id,
        'room': order.room,
        'description': order.description,
        'category': order.category.name if order.category else '',
        'status': order.status,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'completed_at': order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else None,
        'student_id': order.student_id,
        'student_name': order.student.name if order.student else '',
        'student_phone': order.student.phone if order.student else '',
        'repairman_id': order.repairman_id,
        'repairman_name': order.repairman.name if order.repairman else '',
        'images': [img.image_path for img in order.images],
        'comment': comment_info
    }
    
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

# 用户管理API
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'name': u.name,
            'role': u.role,
            'phone': u.phone,
            'email': u.email,
            'avatar': u.avatar,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

@app.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')
    phone = data.get('phone')
    email = data.get('email')
    
    # 验证必填字段
    if not all([username, password, name, role]):
        return jsonify({'code': 400, 'msg': '请填写完整的用户信息'})
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'})
    
    from werkzeug.security import generate_password_hash
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        name=name,
        role=role,
        phone=phone,
        email=email
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户创建成功', 'data': {'user_id': new_user.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '创建失败', 'error': str(e)})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    update_user = User.query.get(user_id)
    if not update_user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    
    data = request.json
    
    # 更新用户信息
    if 'name' in data:
        update_user.name = data['name']
    if 'role' in data:
        update_user.role = data['role']
    if 'phone' in data:
        update_user.phone = data['phone']
    if 'email' in data:
        update_user.email = data['email']
    if 'password' in data and data['password']:
        from werkzeug.security import generate_password_hash
        update_user.password = generate_password_hash(data['password'])
    
    try:
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '更新失败', 'error': str(e)})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    delete_user = User.query.get(user_id)
    if not delete_user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    
    try:
        db.session.delete(delete_user)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败', 'error': str(e)})

# 报修管理API
@app.route('/api/repairs/<int:order_id>/approve', methods=['PUT'])
@jwt_required()
def approve_repair_order(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    order = RepairOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    if order.status != 'pending':
        return jsonify({'code': 400, 'msg': '只有待处理的报修单可以被审核'})
    
    try:
        order.status = 'approved'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '审核通过成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '操作失败', 'error': str(e)})

@app.route('/api/repairs/<int:order_id>/reject', methods=['PUT'])
@jwt_required()
def reject_repair_order(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以访问此功能'})
    
    order = RepairOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    if order.status != 'pending':
        return jsonify({'code': 400, 'msg': '只有待处理的报修单可以被拒绝'})
    
    try:
        order.status = 'rejected'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '拒绝成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '操作失败', 'error': str(e)})

@app.route('/api/repairs/pending', methods=['GET'])
@jwt_required()
def get_pending_repairs():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin' and user.role != 'repairman':
        return jsonify({'code': 403, 'msg': '权限不足'})
    
    orders = RepairOrder.query.filter_by(status='pending').all()
    result = []
    for order in orders:
        result.append({
            'id': order.id,
            'room': order.room,
            'description': order.description,
            'category': order.category.name if order.category else '',
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'student_name': order.student.name if order.student else ''
        })
    
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

# 维修人员接受任务API
@app.route('/api/repairs/<int:order_id>/accept', methods=['PUT'])
@jwt_required()
def accept_repair_task(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'repairman':
        return jsonify({'code': 403, 'msg': '只有维修人员可以接受任务'})
    
    order = RepairOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    if order.status != 'approved':
        return jsonify({'code': 400, 'msg': '只有已审核的报修单可以被接受'})
    
    try:
        order.status = 'repairing'
        order.repairman_id = current_user_id
        db.session.commit()
        return jsonify({'code': 200, 'msg': '任务接受成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '操作失败', 'error': str(e)})

# 维修人员更新维修状态API
@app.route('/api/repairs/<int:order_id>/complete', methods=['PUT'])
@jwt_required()
def complete_repair_task(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'repairman':
        return jsonify({'code': 403, 'msg': '只有维修人员可以完成任务'})
    
    order = RepairOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    if order.status != 'repairing':
        return jsonify({'code': 400, 'msg': '只有维修中的任务可以被完成'})
    
    if order.repairman_id != current_user_id:
        return jsonify({'code': 403, 'msg': '您不是这个任务的负责人'})
    
    try:
        order.status = 'completed'
        order.completed_at = datetime.now()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '任务完成成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '操作失败', 'error': str(e)})

# 管理员公告管理API
@app.route('/api/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    announcements = Announcement.query.all()
    result = []
    for announcement in announcements:
        result.append({
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'created_by': announcement.author.name if announcement.author else '',
            'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': announcement.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

@app.route('/api/announcements', methods=['POST'])
@jwt_required()
def create_announcement():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以发布公告'})
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not all([title, content]):
        return jsonify({'code': 400, 'msg': '请填写完整的公告信息'})
    
    try:
        announcement = Announcement(
            title=title,
            content=content,
            created_by=current_user_id
        )
        db.session.add(announcement)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '公告发布成功', 'data': {'announcement_id': announcement.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '发布失败', 'error': str(e)})

@app.route('/api/announcements/<int:announcement_id>', methods=['PUT'])
@jwt_required()
def update_announcement(announcement_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以编辑公告'})
    
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'code': 404, 'msg': '公告不存在'})
    
    data = request.json
    
    try:
        if 'title' in data:
            announcement.title = data['title']
        if 'content' in data:
            announcement.content = data['content']
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '公告编辑成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '编辑失败', 'error': str(e)})

@app.route('/api/announcements/<int:announcement_id>', methods=['DELETE'])
@jwt_required()
def delete_announcement(announcement_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'code': 403, 'msg': '只有管理员可以删除公告'})
    
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'code': 404, 'msg': '公告不存在'})
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '公告删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '删除失败', 'error': str(e)})

# 学生评价维修服务API
@app.route('/api/comments', methods=['POST'])
@jwt_required()
def create_comment():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'student':
        return jsonify({'code': 403, 'msg': '只有学生可以评价维修服务'})
    
    data = request.json
    repair_order_id = data.get('repair_order_id')
    rating = data.get('rating')
    content = data.get('content')
    
    if not all([repair_order_id, rating]):
        return jsonify({'code': 400, 'msg': '请填写完整的评价信息'})
    
    if rating < 1 or rating > 5:
        return jsonify({'code': 400, 'msg': '评分必须在1-5分之间'})
    
    # 检查报修单是否存在且已完成
    repair_order = RepairOrder.query.get(repair_order_id)
    if not repair_order:
        return jsonify({'code': 404, 'msg': '报修单不存在'})
    
    if repair_order.status != 'completed':
        return jsonify({'code': 400, 'msg': '只能对已完成的维修服务进行评价'})
    
    if repair_order.student_id != current_user_id:
        return jsonify({'code': 403, 'msg': '只能评价自己的报修单'})
    
    # 检查是否已经评价过
    existing_comment = Comment.query.filter_by(repair_order_id=repair_order_id, student_id=current_user_id).first()
    if existing_comment:
        return jsonify({'code': 400, 'msg': '您已经评价过该维修服务'})
    
    try:
        comment = Comment(
            repair_order_id=repair_order_id,
            student_id=current_user_id,
            rating=rating,
            content=content
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '评价成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': '评价失败', 'error': str(e)})

# 获取报修单评价API
@app.route('/api/comments/<int:repair_order_id>', methods=['GET'])
@jwt_required()
def get_comment(repair_order_id):
    comment = Comment.query.filter_by(repair_order_id=repair_order_id).first()
    if not comment:
        return jsonify({'code': 404, 'msg': '该报修单暂无评价'})
    
    result = {
        'id': comment.id,
        'rating': comment.rating,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'student_name': comment.student.name if comment.student else ''
    }
    
    return jsonify({'code': 200, 'msg': '获取成功', 'data': result})

# 运行应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)