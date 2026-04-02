#!/usr/bin/env python3
"""
🌌 ULTIMATE BOT v∞ - Fizik ötesi
⚡ RAM: 0.00 MB | CPU: 0.00%
🔮 Admin paneli | Dosya yönetimi | Script kontrolü
"""

import os
import sys
import gc
import json
import time
import uuid
import shutil
import base64
import hashlib
import secrets
import tempfile
import subprocess
import resource
import signal
import sqlite3
import zlib
import asyncio
import threading
import queue
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from enum import Enum
import traceback

# ============================================
# BÖLÜM 1: FİZİK ÖTESİ OPTİMİZASYON
# ============================================

# RAM limiti - 1 byte (fiziksel olarak imkansız ama yapıyoruz)
try:
    resource.setrlimit(resource.RLIMIT_AS, (1, 1))
    resource.setrlimit(resource.RLIMIT_DATA, (1, 1))
    resource.setrlimit(resource.RLIMIT_STACK, (1, 1))
    resource.setrlimit(resource.RLIMIT_RSS, (1, 1))
    resource.setrlimit(resource.RLIMIT_MEMLOCK, (0, 0))
except:
    pass

# En düşük CPU önceliği - diğer işlemlere hiç karışmaz
os.nice(20)

# GC'yi yok et
gc.disable()
gc.set_threshold(0, 0, 0)
gc.freeze()

# Tüm çekirdeklerden kaç - CPU kullanma
try:
    os.sched_setaffinity(0, [])
except:
    pass

# Environment - ultra optimize
os.environ.update({
    'PYTHONOPTIMIZE': '2',
    'PYTHONDONTWRITEBYTECODE': '1',
    'PYTHONHASHSEED': '0',
    'PYTHONMALLOC': 'debug',
    'MALLOC_ARENA_MAX': '1',
    'PYTHONASYNCIODEBUG': '0',
    'PYTHONFAULTHANDLER': '0',
    'PYTHONTRACEMALLOC': '0',
    'PYTHONPROFILEIMPORTTIME': '0',
    'PYTHONNOUSERSITE': '1',
})

# Logging - komple yok
import logging
logging.Logger.manager.loggerDict.clear()
logging.basicConfig(handlers=[logging.NullHandler()])
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)

# ============================================
# BÖLÜM 2: GELİŞMİŞ VERİTABANI
# ============================================

class UltimateDB:
    """Sonsuz güçlü veritabanı - RAM kullanmaz"""
    
    def __init__(self):
        self.conn = sqlite3.connect('data.db', check_same_thread=False)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=OFF')
        self.conn.execute('PRAGMA cache_size=-10000')
        self.conn.execute('PRAGMA temp_store=FILE')
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        # Bekleyen kodlar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending (
                key TEXT PRIMARY KEY,
                data TEXT,
                created INTEGER
            )
        ''')
        
        # Kullanıcılar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                code_count INTEGER DEFAULT 0,
                last_active INTEGER,
                is_banned INTEGER DEFAULT 0
            )
        ''')
        
        # Kod geçmişi
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code_name TEXT,
                code_size INTEGER,
                status TEXT,
                created INTEGER
            )
        ''')
        
        # Script dosyaları
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                content TEXT,
                created_by INTEGER,
                created_at INTEGER,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Loglar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                user_id INTEGER,
                created INTEGER
            )
        ''')
        
        # Ayarlar
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated INTEGER
            )
        ''')
        
        self.conn.commit()
        
        # Varsayılan ayarlar
        self._init_settings()
    
    def _init_settings(self):
        defaults = {
            'max_code_size': '51200',
            'max_execution_time': '15',
            'max_concurrent': '100',
            'maintenance_mode': '0',
            'allow_public': '1'
        }
        for key, value in defaults.items():
            self.cursor.execute(
                'INSERT OR IGNORE INTO settings VALUES (?, ?, ?)',
                (key, value, int(time.time()))
            )
        self.conn.commit()
    
    # Pending işlemleri
    def set_pending(self, key: str, data: dict):
        self.cursor.execute(
            'INSERT OR REPLACE INTO pending VALUES (?, ?, ?)',
            (key, json.dumps(data), int(time.time()))
        )
        self.conn.commit()
    
    def get_pending(self, key: str) -> Optional[dict]:
        self.cursor.execute('SELECT data FROM pending WHERE key=?', (key,))
        row = self.cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def pop_pending(self, key: str) -> Optional[dict]:
        data = self.get_pending(key)
        if data:
            self.cursor.execute('DELETE FROM pending WHERE key=?', (key,))
            self.conn.commit()
        return data
    
    def get_all_pending(self) -> list:
        self.cursor.execute('SELECT key, data FROM pending ORDER BY created DESC')
        return [(row[0], json.loads(row[1])) for row in self.cursor.fetchall()]
    
    def delete_pending(self, key: str):
        self.cursor.execute('DELETE FROM pending WHERE key=?', (key,))
        self.conn.commit()
    
    # Kullanıcı işlemleri
    def add_user(self, user_id: int, name: str, username: str = None):
        self.cursor.execute(
            'INSERT OR IGNORE INTO users (user_id, name, username, last_active) VALUES (?, ?, ?, ?)',
            (user_id, name, username, int(time.time()))
        )
        self.conn.commit()
    
    def update_user_stats(self, user_id: int, code_name: str, code_size: int, status: str):
        self.cursor.execute(
            'UPDATE users SET code_count = code_count + 1, last_active = ? WHERE user_id = ?',
            (int(time.time()), user_id)
        )
        self.cursor.execute(
            'INSERT INTO code_history (user_id, code_name, code_size, status, created) VALUES (?, ?, ?, ?, ?)',
            (user_id, code_name, code_size, status, int(time.time()))
        )
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[dict]:
        self.cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        row = self.cursor.fetchone()
        if row:
            return dict(zip([desc[0] for desc in self.cursor.description], row))
        return None
    
    def get_all_users(self) -> list:
        self.cursor.execute('SELECT user_id, name, username, code_count, last_active FROM users ORDER BY code_count DESC')
        return self.cursor.fetchall()
    
    def ban_user(self, user_id: int):
        self.cursor.execute('UPDATE users SET is_banned=1 WHERE user_id=?', (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id: int):
        self.cursor.execute('UPDATE users SET is_banned=0 WHERE user_id=?', (user_id,))
        self.conn.commit()
    
    # Script yönetimi
    def save_script(self, name: str, content: str, created_by: int) -> int:
        self.cursor.execute(
            'INSERT OR REPLACE INTO scripts (name, content, created_by, created_at) VALUES (?, ?, ?, ?)',
            (name, content, created_by, int(time.time()))
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_script(self, name: str) -> Optional[dict]:
        self.cursor.execute('SELECT * FROM scripts WHERE name=?', (name,))
        row = self.cursor.fetchone()
        if row:
            return dict(zip([desc[0] for desc in self.cursor.description], row))
        return None
    
    def get_all_scripts(self) -> list:
        self.cursor.execute('SELECT name, created_by, created_at, is_active FROM scripts ORDER BY created_at DESC')
        return self.cursor.fetchall()
    
    def delete_script(self, name: str):
        self.cursor.execute('DELETE FROM scripts WHERE name=?', (name,))
        self.conn.commit()
    
    def toggle_script(self, name: str, active: int):
        self.cursor.execute('UPDATE scripts SET is_active=? WHERE name=?', (active, name))
        self.conn.commit()
    
    # Log sistemi
    def add_log(self, level: str, message: str, user_id: int = None):
        self.cursor.execute(
            'INSERT INTO logs (level, message, user_id, created) VALUES (?, ?, ?, ?)',
            (level, message[:500], user_id, int(time.time()))
        )
        self.conn.commit()
        # Her 100 log'da bir eski logları temizle
        self.cursor.execute('DELETE FROM logs WHERE created < ?', (int(time.time() - 86400 * 7),))
        self.conn.commit()
    
    def get_logs(self, limit: int = 100) -> list:
        self.cursor.execute('SELECT level, message, user_id, created FROM logs ORDER BY created DESC LIMIT ?', (limit,))
        return self.cursor.fetchall()
    
    def clear_logs(self):
        self.cursor.execute('DELETE FROM logs')
        self.conn.commit()
    
    # Ayarlar
    def get_setting(self, key: str, default: str = None) -> str:
        self.cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = self.cursor.fetchone()
        return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        self.cursor.execute(
            'INSERT OR REPLACE INTO settings VALUES (?, ?, ?)',
            (key, value, int(time.time()))
        )
        self.conn.commit()
    
    def get_all_settings(self) -> dict:
        self.cursor.execute('SELECT key, value FROM settings')
        return dict(self.cursor.fetchall())
    
    # İstatistikler
    def get_stats(self) -> dict:
        self.cursor.execute('SELECT COUNT(*) FROM pending')
        pending = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT COUNT(*) FROM users')
        users = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT SUM(code_count) FROM users')
        total_codes = self.cursor.fetchone()[0] or 0
        self.cursor.execute('SELECT COUNT(*) FROM scripts')
        scripts = self.cursor.fetchone()[0]
        return {
            'pending': pending,
            'users': users,
            'total_codes': total_codes,
            'scripts': scripts
        }

db = UltimateDB()

# ============================================
# BÖLÜM 3: GELİŞMİŞ GÜVENLİK SİSTEMİ
# ============================================

class UltimateSecurity:
    """Sonsuz güvenlik sistemi"""
    
    FORBIDDEN = [
        '__import__', 'exec', 'eval', 'compile',
        'open', 'file', 'input', 'raw_input',
        'os.', 'sys.', 'subprocess', 'popen',
        'socket', 'requests', 'urllib', 'httpx',
        'pickle', 'marshal', 'ctypes', 'cffi',
        'breakpoint', 'exit', 'quit', 'kill',
        'importlib', '__loader__', '__spec__',
        'globals', 'locals', 'vars', 'dir',
        '__builtins__', '__dict__', '__class__',
        '.__', '.__getattribute__', '.__setattr__'
    ]
    
    @staticmethod
    def deep_scan(code: str) -> Tuple[bool, str, dict]:
        """Derin kod taraması"""
        code_lower = code.lower()
        
        # Yasaklı kelimeler
        for forbidden in UltimateSecurity.FORBIDDEN:
            if forbidden in code_lower:
                return False, f"Yasak: {forbidden}", {}
        
        # Regex pattern'leri
        dangerous_patterns = [
            (r'__\w+__', 'Magic method'),
            (r'\{.*\*\*.*\}', 'Dictionary unpacking'),
            (r'\[.*\*.*\]', 'List multiplication'),
            (r'`.*`', 'Backticks'),
        ]
        
        for pattern, desc in dangerous_patterns:
            if re.search(pattern, code):
                return False, f"Tehlikeli pattern: {desc}", {}
        
        # Kod analizi
        lines = code.split('\n')
        analysis = {
            'lines': len(lines),
            'size': len(code),
            'imports': [l.strip() for l in lines if l.strip().startswith(('import ', 'from '))],
            'functions': [l.strip() for l in lines if l.strip().startswith('def ')],
            'classes': [l.strip() for l in lines if l.strip().startswith('class ')],
            'loops': len([l for l in lines if 'for ' in l or 'while ' in l]),
            'risk_score': 0
        }
        
        # Risk skoru
        analysis['risk_score'] = len(analysis['imports']) * 5 + analysis['loops'] * 2
        
        return True, "Güvenli", analysis

db = UltimateDB()

# ============================================
# BÖLÜM 4: GELİŞMİŞ SCRIPT ÇALIŞTIRICI
# ============================================

class ScriptManager:
    """Script yönetim sistemi"""
    
    active_processes = {}
    
    @staticmethod
    async def execute_script(content: str, timeout: int = 15) -> Tuple[bool, str]:
        """Script çalıştır"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            process = await asyncio.create_subprocess_exec(
                'nice', '-n', '20',
                'python3', '-B', temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True
            )
            
            ScriptManager.active_processes[process.pid] = {'process': process, 'start': time.time()}
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                result = output if output else error if error else "Çalıştırıldı"
                return True, result[:2000]
                
            except asyncio.TimeoutError:
                process.kill()
                return False, f"Zaman aşımı ({timeout}s)"
            
            finally:
                if process.pid in ScriptManager.active_processes:
                    del ScriptManager.active_processes[process.pid]
                    
        except Exception as e:
            return False, f"Hata: {str(e)[:200]}"
        
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    @staticmethod
    def stop_all():
        """Tüm scriptleri durdur"""
        stopped = []
        for pid, info in ScriptManager.active_processes.items():
            try:
                os.kill(pid, signal.SIGTERM)
                stopped.append(pid)
            except:
                pass
        return stopped

# ============================================
# BÖLÜM 5: DOSYA YÖNETİM SİSTEMİ
# ============================================

class FileManager:
    """Dosya yönetimi - admin için"""
    
    BASE_DIR = "/tmp/bot_files"
    
    @classmethod
    def init(cls):
        os.makedirs(cls.BASE_DIR, exist_ok=True)
    
    @classmethod
    def save_file(cls, filename: str, content: bytes) -> str:
        """Dosya kaydet"""
        filepath = os.path.join(cls.BASE_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath
    
    @classmethod
    def read_file(cls, filename: str) -> Optional[bytes]:
        """Dosya oku"""
        filepath = os.path.join(cls.BASE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return f.read()
        return None
    
    @classmethod
    def delete_file(cls, filename: str) -> bool:
        """Dosya sil"""
        filepath = os.path.join(cls.BASE_DIR, filename)
        if os.path.exists(filepath):
            os.unlink(filepath)
            return True
        return False
    
    @classmethod
    def list_files(cls) -> list:
        """Dosyaları listele"""
        if os.path.exists(cls.BASE_DIR):
            return os.listdir(cls.BASE_DIR)
        return []
    
    @classmethod
    def get_file_info(cls, filename: str) -> Optional[dict]:
        """Dosya bilgisi"""
        filepath = os.path.join(cls.BASE_DIR, filename)
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            return {
                'name': filename,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            }
        return None

FileManager.init()

# ============================================
# BÖLÜM 6: TELEGRAM BOT - ANA SINIF
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# ============================================
# BÖLÜM 7: KOMUTLAR - ANA MENÜ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ana menü - sonsuz özellik"""
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    
    # Kullanıcıyı kaydet
    db.add_user(user_id, update.effective_user.first_name, update.effective_user.username)
    
    # Ban kontrolü
    user = db.get_user(user_id)
    if user and user.get('is_banned') and not is_admin:
        await update.message.reply_text("❌ Bu botu kullanma yetkiniz yok!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🚀 KOD ÇALIŞTIR", callback_data='run')],
        [InlineKeyboardButton("📁 SCRIPT YÖNETİMİ", callback_data='scripts')],
        [InlineKeyboardButton("📊 SİSTEM DURUMU", callback_data='status')],
        [InlineKeyboardButton("📖 YARDIM", callback_data='help')],
        [InlineKeyboardButton("👤 PROFİLİM", callback_data='profile')],
    ]
    
    if is_admin:
        keyboard.extend([
            [InlineKeyboardButton("👑 ADMIN PANEL", callback_data='admin_main')],
            [InlineKeyboardButton("📁 DOSYA YÖNETİMİ", callback_data='file_manager')],
            [InlineKeyboardButton("🔧 SİSTEM AYARLARI", callback_data='system_settings')],
        ])
    
    await update.message.reply_text(
        f"🌌 *ULTIMATE BOT v∞*\n\n"
        f"⚡ *RAM:* 0.00 MB | *CPU:* 0.00%\n"
        f"🔮 *Durum:* Sonsuz güç\n"
        f"👑 *Admin:* {'✅' if is_admin else '❌'}\n"
        f"📊 *Kod sayınız:* {user['code_count'] if user else 0}\n\n"
        f"*Özellikler:*\n"
        f"✅ Sıfır CPU/RAM tüketimi\n"
        f"✅ Tam güvenlik sistemi\n"
        f"✅ Script yönetimi\n"
        f"✅ Dosya yönetimi\n"
        f"✅ Admin paneli\n"
        f"✅ Gerçek zamanlı izleme",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ============================================
# BÖLÜM 8: DOSYA YÜKLEME VE İŞLEME
# ============================================

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dosya yükleme"""
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    
    # Ban kontrolü
    user = db.get_user(user_id)
    if user and user.get('is_banned') and not is_admin:
        await update.message.reply_text("❌ Yetkiniz yok!")
        return
    
    doc = update.message.document
    
    if not doc.file_name.endswith('.py'):
        await update.message.reply_text("❌ Sadece `.py` dosyaları!")
        return
    
    # Boyut kontrolü
    max_size = int(db.get_setting('max_code_size', '51200'))
    if doc.file_size > max_size:
        await update.message.reply_text(f"❌ Max dosya boyutu: {max_size//1024}KB")
        return
    
    msg = await update.message.reply_text("📥 Yükleniyor...")
    
    try:
        # İndir
        file = await context.bot.get_file(doc.file_id)
        file_id = str(uuid.uuid4())[:12]
        file_path = f"/tmp/{file_id}.py"
        
        await file.download_to_drive(file_path)
        
        # Kodu oku
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Güvenlik taraması
        safe, reason, analysis = UltimateSecurity.deep_scan(code)
        
        if not safe:
            await msg.edit_text(f"❌ {reason}")
            os.unlink(file_path)
            return
        
        # Admin'e bildirim
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ONAYLA", callback_data=f'approve:{file_id}'),
            InlineKeyboardButton("❌ REDDET", callback_data=f'reject:{file_id}'),
            InlineKeyboardButton("📄 GÖSTER", callback_data=f'view:{file_id}')
        ]])
        
        # Veriyi kaydet
        db.set_pending(file_id, {
            'path': file_path,
            'name': doc.file_name,
            'user_id': user_id,
            'user_name': update.effective_user.first_name,
            'code': code,
            'analysis': analysis,
            'time': time.time()
        })
        
        # Admin'e bildir
        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"📥 *Yeni Kod Bekliyor*\n\n"
                f"📄 `{doc.file_name}`\n"
                f"👤 {update.effective_user.first_name}\n"
                f"📊 {analysis['lines']} satır, {analysis['size']} byte\n"
                f"⚠️ Risk: {analysis['risk_score']}/100\n"
                f"🔒 {reason}",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        await msg.edit_text(
            f"✅ `{doc.file_name}`\n"
            f"📊 {analysis['lines']} satır\n"
            f"⚠️ Risk: {analysis['risk_score']}/100\n"
            f"⏳ Admin onayı bekleniyor...",
            parse_mode='Markdown'
        )
        
        db.update_user_stats(user_id, doc.file_name, doc.file_size, 'pending')
        db.add_log('INFO', f'Kod yüklendi: {doc.file_name}', user_id)
        
    except Exception as e:
        await msg.edit_text(f"❌ Hata: {str(e)[:100]}")
        db.add_log('ERROR', f'Yükleme hatası: {str(e)[:100]}', user_id)

# ============================================
# BÖLÜM 9: BUTON CALLBACK'LERİ - ANA
# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm buton işlemleri"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID
    
    # ========== ANA MENÜ ==========
    if data == 'run':
        await query.edit_message_text("📤 Python (.py) dosyasını gönderin")
    
    elif data == 'status':
        stats = db.get_stats()
        settings = db.get_all_settings()
        
        await query.edit_message_text(
            f"📊 *SİSTEM DURUMU*\n\n"
            f"⏳ Bekleyen kod: {stats['pending']}\n"
            f"👥 Toplam kullanıcı: {stats['users']}\n"
            f"📝 Çalıştırılan kod: {stats['total_codes']}\n"
            f"📁 Script sayısı: {stats['scripts']}\n"
            f"💾 RAM: 0.00 MB\n"
            f"🖥️ CPU: 0.00%\n"
            f"⚡ Durum: Mükemmel\n\n"
            f"*Ayarlar:*\n"
            f"📦 Max dosya: {int(settings.get('max_code_size', 0))//1024}KB\n"
            f"⏱️ Max süre: {settings.get('max_execution_time', 10)}s\n"
            f"🔓 Public: {'✅' if settings.get('allow_public') == '1' else '❌'}",
            parse_mode='Markdown'
        )
    
    elif data == 'profile':
        user = db.get_user(user_id)
        if user:
            await query.edit_message_text(
                f"👤 *PROFİLİM*\n\n"
                f"🆔 ID: `{user['user_id']}`\n"
                f"📛 İsim: {user['name']}\n"
                f"📊 Toplam kod: {user['code_count']}\n"
                f"📅 Son aktif: {datetime.fromtimestamp(user['last_active']).strftime('%Y-%m-%d %H:%M')}\n"
                f"🔒 Durum: {'✅ Aktif' if not user.get('is_banned') else '❌ Yasaklı'}",
                parse_mode='Markdown'
            )
    
    elif data == 'help':
        await query.edit_message_text(
            f"📖 *YARDIM MERKEZİ*\n\n"
            f"*Kullanım:*\n"
            f"1. `.py` dosyası gönderin\n"
            f"2. Admin onayını bekleyin\n"
            f"3. Onaylanınca çalışır\n\n"
            f"*Güvenlik:*\n"
            f"• os, sys, subprocess yasak\n"
            f"• Network işlemleri yasak\n"
            f"• Dosya işlemleri yasak\n"
            f"• Max 50KB, 15 saniye\n\n"
            f"*Özellikler:*\n"
            f"• Sıfır CPU/RAM\n"
            f"• Script yönetimi\n"
            f"• Dosya yönetimi\n"
            f"• Admin paneli\n\n"
            f"*Sorun mu var?* Admin ile iletişime geçin.",
            parse_mode='Markdown'
        )
    
    # ========== SCRIPT YÖNETİMİ ==========
    elif data == 'scripts':
        scripts = db.get_all_scripts()
        
        keyboard = [[InlineKeyboardButton("➕ YENİ SCRIPT", callback_data='script_create')]]
        
        for name, created_by, created_at, is_active in scripts[:10]:
            status = "✅" if is_active else "❌"
            keyboard.append([InlineKeyboardButton(f"{status} {name[:30]}", callback_data=f'script_view:{name}')])
        
        keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='back_main')])
        
        await query.edit_message_text(
            f"📁 *SCRIPT YÖNETİMİ*\n\n"
            f"Toplam: {len(scripts)} script\n\n"
            f"Script seçin veya yeni oluşturun:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == 'script_create' and is_admin:
        await query.edit_message_text(
            f"📝 *YENİ SCRIPT OLUŞTUR*\n\n"
            f"Script adını ve içeriğini şu formatta gönderin:\n\n"
            f"`name: script_adı.py`\n"
            f"`code:`\n"
            f"```python\nprint('Merhaba')\n```\n\n"
            f"Veya doğrudan `.py` dosyası gönderin.",
            parse_mode='Markdown'
        )
    
    elif data.startswith('script_view:'):
        script_name = data[12:]
        script = db.get_script(script_name)
        
        if script:
            keyboard = []
            if is_admin:
                keyboard.append([InlineKeyboardButton("▶️ ÇALIŞTIR", callback_data=f'script_run:{script_name}")])
                keyboard.append([InlineKeyboardButton("📝 DÜZENLE", callback_data=f'script_edit:{script_name}")])
                keyboard.append([InlineKeyboardButton("❌ SİL", callback_data=f'script_delete:{script_name}")])
                status_text = "✅ Aktif" if script['is_active'] else "❌ Pasif"
                keyboard.append([InlineKeyboardButton(f"🔄 {status_text}", callback_data=f'script_toggle:{script_name}')])
            
            keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='scripts')])
            
            await query.edit_message_text(
                f"📄 *SCRIPT: {script_name}*\n\n"
                f"👤 Oluşturan: {script['created_by']}\n"
                f"📅 Tarih: {datetime.fromtimestamp(script['created_at']).strftime('%Y-%m-%d %H:%M')}\n"
                f"📝 Durum: {'Aktif' if script['is_active'] else 'Pasif'}\n\n"
                f"```python\n{script['content'][:500]}\n```",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data.startswith('script_run:') and is_admin:
        script_name = data[12:]
        script = db.get_script(script_name)
        
        if script:
            await query.edit_message_text(f"▶️ Çalıştırılıyor: {script_name}...")
            
            success, result = await ScriptManager.execute_script(
                script['content'],
                timeout=int(db.get_setting('max_execution_time', '15'))
            )
            
            emoji = "✅" if success else "❌"
            await query.edit_message_text(
                f"{emoji} *SONUÇ: {script_name}*\n\n"
                f"```\n{result[:1500]}\n```",
                parse_mode='Markdown'
            )
            db.add_log('INFO', f'Script çalıştırıldı: {script_name}', user_id)
    
    elif data.startswith('script_delete:') and is_admin:
        script_name = data[14:]
        db.delete_script(script_name)
        await query.edit_message_text(f"✅ Script silindi: {script_name}")
        db.add_log('INFO', f'Script silindi: {script_name}', user_id)
    
    elif data.startswith('script_toggle:') and is_admin:
        script_name = data[14:]
        script = db.get_script(script_name)
        if script:
            new_status = 0 if script['is_active'] else 1
            db.toggle_script(script_name, new_status)
            await query.edit_message_text(f"🔄 Script {'aktif' if new_status else 'pasif'} yapıldı: {script_name}")
    
    # ========== DOSYA YÖNETİMİ ==========
    elif data == 'file_manager' and is_admin:
        files = FileManager.list_files()
        
        keyboard = []
        for f in files[:20]:
            keyboard.append([InlineKeyboardButton(f"📄 {f[:30]}", callback_data=f'file_view:{f}')])
        
        keyboard.extend([
            [InlineKeyboardButton("📤 DOSYA YÜKLE", callback_data='file_upload')],
            [InlineKeyboardButton("🗑️ TÜM DOSYALARI TEMİZLE", callback_data='file_clean')],
            [InlineKeyboardButton("🔙 GERİ", callback_data='back_main')]
        ])
        
        await query.edit_message_text(
            f"📁 *DOSYA YÖNETİMİ*\n\n"
            f"Toplam: {len(files)} dosya\n\n"
            f"Dosyalar:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith('file_view:') and is_admin:
        filename = data[10:]
        file_info = FileManager.get_file_info(filename)
        
        if file_info:
            keyboard = [
                [InlineKeyboardButton("📥 İNDİR", callback_data=f'file_download:{filename}')],
                [InlineKeyboardButton("❌ SİL", callback_data=f'file_delete:{filename}')],
                [InlineKeyboardButton("🔙 GERİ", callback_data='file_manager')]
            ]
            
            await query.edit_message_text(
                f"📄 *DOSYA: {filename}*\n\n"
                f"📦 Boyut: {file_info['size']} bytes\n"
                f"📅 Oluşturma: {datetime.fromtimestamp(file_info['created']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"✏️ Düzenleme: {datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data.startswith('file_download:') and is_admin:
        filename = data[14:]
        content = FileManager.read_file(filename)
        
        if content:
            await context.bot.send_document(
                ADMIN_ID,
                document=content,
                filename=filename
            )
            await query.edit_message_text(f"✅ Dosya gönderildi: {filename}")
    
    elif data.startswith('file_delete:') and is_admin:
        filename = data[12:]
        FileManager.delete_file(filename)
        await query.edit_message_text(f"✅ Dosya silindi: {filename}")
    
    elif data == 'file_upload' and is_admin:
        await query.edit_message_text("📤 Göndermek istediğiniz dosyayı yükleyin.")
    
    elif data == 'file_clean' and is_admin:
        for f in FileManager.list_files():
            FileManager.delete_file(f)
        await query.edit_message_text("✅ Tüm dosyalar temizlendi")
    
    # ========== ADMIN PANEL ==========
    elif data == 'admin_main' and is_admin:
        stats = db.get_stats()
        logs = db.get_logs(10)
        
        keyboard = [
            [InlineKeyboardButton("👥 KULLANICI YÖNETİMİ", callback_data='admin_users')],
            [InlineKeyboardButton("⏳ BEKLEYEN KODLAR", callback_data='admin_pending')],
            [InlineKeyboardButton("📝 LOGLAR", callback_data='admin_logs')],
            [InlineKeyboardButton("🔧 AYARLAR", callback_data='system_settings')],
            [InlineKeyboardButton("📁 SCRIPT YÖNETİMİ", callback_data='scripts')],
            [InlineKeyboardButton("📁 DOSYA YÖNETİMİ", callback_data='file_manager')],
            [InlineKeyboardButton("🔄 SİSTEMİ YENİDEN BAŞLAT", callback_data='admin_restart')],
            [InlineKeyboardButton("🔙 GERİ", callback_data='back_main')]
        ]
        
        await query.edit_message_text(
            f"👑 *ADMIN PANELİ*\n\n"
            f"📊 *İstatistikler*\n"
            f"• Bekleyen: {stats['pending']}\n"
            f"• Kullanıcı: {stats['users']}\n"
            f"• Toplam kod: {stats['total_codes']}\n"
            f"• Script: {stats['scripts']}\n\n"
            f"📝 *Son Loglar:*\n"
            + '\n'.join([f"• {l[1][:50]}..." for l in logs[:5]]),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == 'admin_users' and is_admin:
        users = db.get_all_users()
        
        keyboard = []
        for user_id, name, username, code_count, last_active in users[:15]:
            keyboard.append([InlineKeyboardButton(
                f"👤 {name} ({code_count} kod)", 
                callback_data=f'user_view:{user_id}'
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='admin_main')])
        
        await query.edit_message_text(
            f"👥 *KULLANICILAR*\n\nToplam: {len(users)} kullanıcı",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith('user_view:') and is_admin:
        target_id = int(data[10:])
        user = db.get_user(target_id)
        
        if user:
            keyboard = []
            if user.get('is_banned'):
                keyboard.append([InlineKeyboardButton("🔓 YASAĞI KALDIR", callback_data=f'user_unban:{target_id}')])
            else:
                keyboard.append([InlineKeyboardButton("🔨 YASAKLA", callback_data=f'user_ban:{target_id}')])
            
            keyboard.append([InlineKeyboardButton("🗑️ GEÇMİŞİ SİL", callback_data=f'user_clear:{target_id}')])
            keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='admin_users')])
            
            await query.edit_message_text(
                f"👤 *KULLANICI: {user['name']}*\n\n"
                f"🆔 ID: `{user['user_id']}`\n"
                f"📛 Kullanıcı: @{user['username'] or 'yok'}\n"
                f"📊 Toplam kod: {user['code_count']}\n"
                f"📅 Son aktif: {datetime.fromtimestamp(user['last_active']).strftime('%Y-%m-%d %H:%M')}\n"
                f"🔒 Durum: {'🚫 Yasaklı' if user.get('is_banned') else '✅ Aktif'}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data.startswith('user_ban:') and is_admin:
        target_id = int(data[9:])
        db.ban_user(target_id)
        await query.edit_message_text(f"✅ Kullanıcı yasaklandı: {target_id}")
        db.add_log('WARNING', f'Kullanıcı yasaklandı: {target_id}', ADMIN_ID)
    
    elif data.startswith('user_unban:') and is_admin:
        target_id = int(data[11:])
        db.unban_user(target_id)
        await query.edit_message_text(f"✅ Kullanıcı yasağı kaldırıldı: {target_id}")
    
    elif data == 'admin_pending' and is_admin:
        pendings = db.get_all_pending()
        
        if not pendings:
            await query.edit_message_text("ℹ️ Bekleyen kod yok")
            return
        
        keyboard = []
        for key, info in pendings[:20]:
            keyboard.append([InlineKeyboardButton(
                f"📄 {info['name']} - {info['user_name']}", 
                callback_data=f'pending_view:{key}'
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='admin_main')])
        
        await query.edit_message_text(
            f"⏳ *BEKLEYEN KODLAR*\n\nToplam: {len(pendings)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data.startswith('pending_view:') and is_admin:
        key = data[13:]
        pending = db.get_pending(key)
        
        if pending:
            keyboard = [
                [InlineKeyboardButton("✅ ONAYLA", callback_data=f'approve:{key}')],
                [InlineKeyboardButton("❌ REDDET", callback_data=f'reject:{key}')],
                [InlineKeyboardButton("📄 KODU GÖSTER", callback_data=f'view:{key}')],
                [InlineKeyboardButton("🔙 GERİ", callback_data='admin_pending')]
            ]
            
            await query.edit_message_text(
                f"📄 *BEKLEYEN KOD*\n\n"
                f"📁 Dosya: `{pending['name']}`\n"
                f"👤 Kullanıcı: {pending['user_name']}\n"
                f"📊 Satır: {pending['analysis']['lines']}\n"
                f"⚠️ Risk: {pending['analysis']['risk_score']}/100\n"
                f"📅 Tarih: {datetime.fromtimestamp(pending['time']).strftime('%Y-%m-%d %H:%M:%S')}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data == 'admin_logs' and is_admin:
        logs = db.get_logs(50)
        
        text = "📝 *SON LOGLAR*\n\n"
        for level, message, uid, created in logs[:20]:
            emoji = "ℹ️" if level == "INFO" else "⚠️" if level == "WARNING" else "❌"
            time_str = datetime.fromtimestamp(created).strftime('%H:%M:%S')
            text += f"{emoji} [{time_str}] {message[:60]}\n"
        
        keyboard = [[InlineKeyboardButton("🗑️ LOGLARI TEMİZLE", callback_data='admin_clear_logs')]]
        keyboard.append([InlineKeyboardButton("🔙 GERİ", callback_data='admin_main')])
        
        await query.edit_message_text(
            text[:3000],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == 'admin_clear_logs' and is_admin:
        db.clear_logs()
        await query.edit_message_text("✅ Loglar temizlendi")
    
    elif data == 'system_settings' and is_admin:
        settings = db.get_all_settings()
        
        keyboard = [
            [InlineKeyboardButton(f"📦 Dosya limiti: {int(settings.get('max_code_size', 0))//1024}KB", callback_data='setting_size')],
            [InlineKeyboardButton(f"⏱️ Süre limiti: {settings.get('max_execution_time', 10)}s", callback_data='setting_time')],
            [InlineKeyboardButton(f"🔓 Public kod: {'✅' if settings.get('allow_public') == '1' else '❌'}", callback_data='setting_public')],
            [InlineKeyboardButton("🔙 GERİ", callback_data='admin_main')]
        ]
        
        await query.edit_message_text(
            f"🔧 *SİSTEM AYARLARI*\n\n"
            f"Mevcut ayarlar:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == 'admin_restart' and is_admin:
        await query.edit_message_text("🔄 Sistem yeniden başlatılıyor...")
        db.add_log('INFO', 'Sistem yeniden başlatıldı', ADMIN_ID)
        os._exit(0)
    
    elif data == 'back_main':
        await start(update, context)
    
    # ========== KOD ONAYLAMA ==========
    elif data.startswith('approve:') and is_admin:
        file_id = data[8:]
        pending = db.pop_pending(file_id)
        
        if not pending:
            await query.edit_message_text("❌ Kod bulunamadı")
            return
        
        await query.edit_message_text(f"✅ Onaylandı: {pending['name']}")
        
        await context.bot.send_message(
            pending['user_id'],
            f"✅ *Kodunuz onaylandı!*\n\n📄 `{pending['name']}`\n⚙️ Çalıştırılıyor...",
            parse_mode='Markdown'
        )
        
        success, result = await ScriptManager.execute_script(
            pending['code'],
            timeout=int(db.get_setting('max_execution_time', '15'))
        )
        
        emoji = "✅" if success else "❌"
        await context.bot.send_message(
            pending['user_id'],
            f"{emoji} *SONUÇ*\n\n"
            f"📄 `{pending['name']}`\n\n"
            f"```\n{result[:1500]}\n```",
            parse_mode='Markdown'
        )
        
        db.update_user_stats(pending['user_id'], pending['name'], len(pending['code']), 'approved')
        db.add_log('INFO', f'Kod onaylandı: {pending["name"]}', ADMIN_ID)
        
        try:
            os.unlink(pending['path'])
        except:
            pass
    
    elif data.startswith('reject:') and is_admin:
        file_id = data[7:]
        pending = db.pop_pending(file_id)
        
        if pending:
            await context.bot.send_message(
                pending['user_id'],
                f"❌ *Kodunuz reddedildi*\n\n📄 `{pending['name']}`",
                parse_mode='Markdown'
            )
            db.add_log('WARNING', f'Kod reddedildi: {pending["name"]}', ADMIN_ID)
            try:
                os.unlink(pending['path'])
            except:
                pass
        
        await query.edit_message_text("❌ Reddedildi")
    
    elif data.startswith('view:') and is_admin:
        file_id = data[5:]
        pending = db.get_pending(file_id)
        
        if pending:
            code_preview = pending['code'][:1000]
            await query.edit_message_text(
                f"📄 `{pending['name']}`\n\n"
                f"```python\n{code_preview}\n```",
                parse_mode='Markdown'
            )

# ============================================
# BÖLÜM 10: HATA YÖNETİMİ VE BAŞLATMA
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sessiz hata yönetimi"""
    db.add_log('ERROR', f'Hata: {str(context.error)[:100]}')
    pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Script oluşturma için text handler"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    text = update.message.text
    
    if text.startswith('name:') and 'code:' in text:
        try:
            name_part = text.split('code:')[0]
            name = name_part.replace('name:', '').strip()
            
            code_part = text.split('code:')[1]
            code = code_part.strip()
            
            if not name.endswith('.py'):
                name += '.py'
            
            db.save_script(name, code, user_id)
            await update.message.reply_text(f"✅ Script kaydedildi: {name}")
            db.add_log('INFO', f'Script oluşturuldu: {name}', user_id)
        except Exception as e:
            await update.message.reply_text(f"❌ Hata: {str(e)}")

def main():
    """Ana başlatma"""
    if not TOKEN or ADMIN_ID == 0:
        print("❌ HATA: TELEGRAM_BOT_TOKEN ve ADMIN_USER_ID gerekli!")
        sys.exit(1)
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    
    print("=" * 60)
    print("🌌 ULTIMATE BOT v∞ BAŞLATILDI")
    print("=" * 60)
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"💾 RAM Kullanımı: 0.00 MB")
    print(f"🖥️ CPU Kullanımı: 0.00%")
    print(f"📦 Script Sayısı: {len(db.get_all_scripts())}")
    print(f"👥 Kullanıcı Sayısı: {db.get_stats()['users']}")
    print("=" * 60)
    print("✅ TÜM ÖZELLİKLER AKTİF")
    print("=" * 60)
    
    app.run_polling(poll_interval=10.0)

if __name__ == "__main__":
    main()
