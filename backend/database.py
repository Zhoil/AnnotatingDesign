import sqlite3
import json
from datetime import datetime
import os

class Database:
    """数据库管理类"""
    
    def __init__(self, db_path='analysis.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建分析记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_text TEXT NOT NULL,
                analysis_result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, filename, original_text, analysis_result):
        """保存分析结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_records (filename, original_text, analysis_result)
            VALUES (?, ?, ?)
        ''', (filename, original_text, json.dumps(analysis_result, ensure_ascii=False)))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_history(self, page=1, per_page=10):
        """获取历史记录列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute('SELECT COUNT(*) FROM analysis_records')
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, filename, created_at, analysis_result
            FROM analysis_records
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        rows = cursor.fetchall()
        records = []
        
        for row in rows:
            analysis_result = json.loads(row[3])
            records.append({
                'id': row[0],
                'filename': row[1],
                'created_at': row[2],
                'title': analysis_result.get('title', row[1]),
                'keypoint_count': len(analysis_result.get('keypoints', [])),
                'word_count': analysis_result.get('statistics', {}).get('word_count', 0)
            })
        
        conn.close()
        
        return {
            'records': records,
            'total': total
        }
    
    def get_record(self, record_id):
        """获取单条记录详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, original_text, analysis_result, created_at
            FROM analysis_records
            WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        analysis_result = json.loads(row[3])
        
        return {
            'id': row[0],
            'filename': row[1],
            'content': row[2],
            'title': analysis_result.get('title', row[1]),
            'keypoints': analysis_result.get('keypoints', []),
            'summary': analysis_result.get('summary', {}),
            'statistics': analysis_result.get('statistics', {}),
            'highlights': analysis_result.get('highlights', []),
            'annotated_url': analysis_result.get('annotated_url'), # 提取标注URL
            'created_at': row[4],
            'analysis_result': analysis_result
        }
    
    def delete_record(self, record_id):
        """删除记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analysis_records WHERE id = ?', (record_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def search_records(self, keyword):
        """搜索记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, created_at, analysis_result
            FROM analysis_records
            WHERE filename LIKE ? OR original_text LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%'))
        
        rows = cursor.fetchall()
        records = []
        
        for row in rows:
            analysis_result = json.loads(row[3])
            records.append({
                'id': row[0],
                'filename': row[1],
                'created_at': row[2],
                'title': analysis_result.get('title', row[1])
            })
        
        conn.close()
        
        return records
