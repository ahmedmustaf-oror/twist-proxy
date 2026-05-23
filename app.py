from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import logging
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# ==============================================
# إعدادات CORS المتقدمة - حل مشكلة Forbidden
# ==============================================
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.after_request
def after_request(response):
    """إضافة هيدرز CORS بعد كل طلب"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

# معالجة طلبات OPTIONS (preflight) لجميع المسارات
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """الرد على طلبات OPTIONS المسبقة"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response, 200

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعدادات API
API_BASE_URL = "https://api.twistmena.com"
REQUEST_TIMEOUT = 30

# ==============================================
# دوال مساعدة
# ==============================================

def get_default_headers():
    """هيدرز افتراضية لمحاكاة طلب حقيقي"""
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "ar,en;q=0.9",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Host": "api.twistmena.com",
        "Origin": "https://twistmena.com",
        "Referer": "https://twistmena.com/"
    }

def format_phone(phone):
    """تنسيق رقم الهاتف"""
    phone = phone.strip()
    if phone.startswith('01'):
        phone = '2' + phone
    elif phone.startswith('0'):
        phone = '2' + phone
    return phone

# ==============================================
# الصفحة الرئيسية
# ==============================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "name": "OROR TWIST API Proxy",
        "version": "2.0.0",
        "server": "Vercel + Python",
        "endpoints": [
            {"path": "/send_otp", "method": "POST", "description": "إرسال كود التحقق"},
            {"path": "/verify_otp", "method": "POST", "description": "التحقق من الكود"},
            {"path": "/get_balance", "method": "POST", "description": "جلب الرصيد"},
            {"path": "/complete_tasks", "method": "POST", "description": "إنجاز المهام"},
            {"path": "/redeem", "method": "POST", "description": "سحب الوحدات"},
            {"path": "/delete_account", "method": "POST", "description": "حذف الحساب"},
            {"path": "/health", "method": "GET", "description": "فحص صحة الخادم"}
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """فحص صحة الخادم"""
    return jsonify({
        "status": "healthy",
        "proxy": "working",
        "timestamp": datetime.now().isoformat()
    })

# ==============================================
# 1. إرسال كود OTP
# ==============================================

@app.route('/send_otp', methods=['POST', 'OPTIONS'])
def send_otp():
    if request.method == 'OPTIONS':
        return handle_options('send_otp')
    
    try:
        data = request.get_json()
        phone = data.get('phone', '')
        
        if not phone:
            return jsonify({
                "success": False,
                "message": "❌ رقم الهاتف مطلوب"
            }), 400
        
        phone = format_phone(phone)
        headers = get_default_headers()
        
        logger.info(f"Sending OTP to: {phone}")
        
        response = requests.post(
            f"{API_BASE_URL}/music/Dlogin/sendCode",
            headers=headers,
            json={"dial": phone},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            logger.info(f"OTP sent successfully to: {phone}")
            return jsonify({
                "success": True,
                "message": "✅ تم إرسال الكود بنجاح",
                "phone": phone
            })
        else:
            logger.error(f"Send OTP failed: {response.text}")
            return jsonify({
                "success": False,
                "message": f"❌ فشل إرسال الكود"
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "⏱️ انتهت مهلة الاتصال"
        }), 408
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# 2. التحقق من كود OTP
# ==============================================

@app.route('/verify_otp', methods=['POST', 'OPTIONS'])
def verify_otp():
    if request.method == 'OPTIONS':
        return handle_options('verify_otp')
    
    try:
        data = request.get_json()
        phone = data.get('phone', '')
        code = data.get('code', '')
        
        if not phone or not code:
            return jsonify({
                "success": False,
                "message": "❌ رقم الهاتف والكود مطلوبان"
            }), 400
        
        phone = format_phone(phone)
        headers = get_default_headers()
        
        logger.info(f"Verifying OTP for: {phone}")
        
        response = requests.post(
            f"{API_BASE_URL}/music/Dlogin/verify",
            headers=headers,
            json={
                "dial": phone,
                "verifyCode": code,
                "socialServiceName": "",
                "socialServiceToken": ""
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            resp_data = response.json()
            token = resp_data.get('token') or resp_data.get('authorization')
            
            if token:
                token = token.replace('Bearer ', '')
                logger.info(f"User verified successfully: {phone}")
                return jsonify({
                    "success": True,
                    "message": "✅ تم تسجيل الدخول بنجاح",
                    "token": token,
                    "access_token": resp_data.get('accessToken', '')
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "⚠️ لم يتم استلام التوكن"
                })
        else:
            logger.error(f"Verify OTP failed: {response.text}")
            return jsonify({
                "success": False,
                "message": "❌ كود التحقق غير صحيح"
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# 3. جلب الرصيد
# ==============================================

@app.route('/get_balance', methods=['POST', 'OPTIONS'])
def get_balance():
    if request.method == 'OPTIONS':
        return handle_options('get_balance')
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({
                "success": False,
                "message": "❌ التوكن مطلوب"
            }), 400
        
        headers = get_default_headers()
        headers['authorization'] = f'Bearer {token}'
        
        response = requests.get(
            f"{API_BASE_URL}/music/user/loyalty/balance/details",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            balance = response.json().get('balance', 0)
            return jsonify({
                "success": True,
                "balance": balance
            })
        else:
            return jsonify({
                "success": False,
                "message": "انتهت صلاحية التوكن",
                "logout": True
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Get balance error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# 4. إنجاز المهام
# ==============================================

@app.route('/complete_tasks', methods=['POST', 'OPTIONS'])
def complete_tasks():
    if request.method == 'OPTIONS':
        return handle_options('complete_tasks')
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({
                "success": False,
                "message": "❌ التوكن مطلوب"
            }), 400
        
        headers = get_default_headers()
        headers['authorization'] = f'Bearer {token}'
        
        completed = 0
        earned = 0
        
        # جلب قائمة المهام
        tasks_response = requests.get(
            f"{API_BASE_URL}/music/user/loyalty/achievements/v2",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        achievements = []
        
        if tasks_response.status_code == 200:
            tasks_data = tasks_response.json()
            achievements = tasks_data.get('badges', [])
            
            for category in tasks_data.get('badges', []):
                for task in category.get('badges', []):
                    if not task.get('rewarded'):
                        try:
                            action_response = requests.post(
                                f"{API_BASE_URL}/music/loyalty/action/{task.get('id')}",
                                headers=headers,
                                timeout=10
                            )
                            if action_response.status_code == 200:
                                completed += 1
                                earned += task.get('reward', 0)
                                logger.info(f"Task completed: {task.get('title')}")
                        except Exception as e:
                            logger.warning(f"Task failed: {str(e)}")
                            pass
        
        # تحديث الرصيد
        balance_response = requests.get(
            f"{API_BASE_URL}/music/user/loyalty/balance/details",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        new_balance = balance_response.json().get('balance', 0) if balance_response.status_code == 200 else 0
        
        logger.info(f"Tasks completed: {completed}, earned: {earned}")
        
        return jsonify({
            "success": True,
            "completed": completed,
            "earned": earned,
            "new_balance": new_balance,
            "achievements": achievements,
            "message": f"✅ تم إنجاز {completed} مهمة وربح {earned} كوينز"
        })
        
    except Exception as e:
        logger.error(f"Complete tasks error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# 5. سحب الوحدات
# ==============================================

@app.route('/redeem', methods=['POST', 'OPTIONS'])
def redeem():
    if request.method == 'OPTIONS':
        return handle_options('redeem')
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        package_id = data.get('package_id', '')
        
        if not token or not package_id:
            return jsonify({
                "success": False,
                "message": "❌ التوكن والباقة مطلوبان"
            }), 400
        
        headers = get_default_headers()
        headers['authorization'] = f'Bearer {token}'
        
        response = requests.post(
            f"{API_BASE_URL}/music/loyalty/redeem/{package_id}",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            logger.info(f"Redeemed package: {package_id}")
            return jsonify({
                "success": True,
                "message": "✅ تم السحب بنجاح!"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"❌ فشل السحب"
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Redeem error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# 6. حذف الحساب
# ==============================================

@app.route('/delete_account', methods=['POST', 'OPTIONS'])
def delete_account():
    if request.method == 'OPTIONS':
        return handle_options('delete_account')
    
    try:
        data = request.get_json()
        token = data.get('token', '')
        
        if not token:
            return jsonify({
                "success": False,
                "message": "❌ التوكن مطلوب"
            }), 400
        
        headers = get_default_headers()
        headers['authorization'] = f'Bearer {token}'
        
        response = requests.delete(
            f"{API_BASE_URL}/music/user/deleteAccount",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code in [200, 204]:
            logger.info("Account deleted successfully")
            return jsonify({
                "success": True,
                "message": "✅ تم حذف الحساب بنجاح"
            })
        else:
            return jsonify({
                "success": False,
                "message": "❌ فشل حذف الحساب"
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"❌ خطأ: {str(e)[:100]}"
        }), 500

# ==============================================
# تشغيل التطبيق
# ==============================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)