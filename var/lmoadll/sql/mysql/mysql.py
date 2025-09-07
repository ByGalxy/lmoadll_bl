import pymysql

def sc_verification_db_conn(db_host, db_port, db_name, db_user, db_password):
    try:
        db = pymysql.connect(
                host=db_host,
                port=int(db_port),
                user=db_user,
                password=db_password,
                database=db_name,  # 使用传入的数据库名参数
                charset='utf8mb4',  # 添加字符集设置
            )
        cursor = db.cursor()
        cursor.execute('SELECT VERSION()')

        cursor.close()
        db.close()

        return [True, 0]
    
    except pymysql.Error as e:
        return [False, e]
