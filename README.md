flashback
========================

从MySQL binlog解析出你要的SQL。根据不同选项，你可以得到原始SQL、回滚SQL、去除主键的INSERT SQL等。

用途
===========

* 数据快速回滚(闪回)
* 主从切换后新master丢数据的修复
* 从binlog生成标准SQL，带来的衍生功能

* 需求环境
    * Python 3.5
    * MySQL 5.6+


安装
==============

```
shell> git clone http://gitlab.mljr.com/hackthon/flashback && cd flashback
shell> pip3 install pymysql
```
git与pip的安装问题请自行搜索解决。

使用
=========

### MySQL server必须设置以下参数:

    [mysqld]
    server_id = 1
    log_bin = [binlog_path]
    binlog_format = row

### user需要的最小权限集合：

    select, super/replication client, replication slave
    
    建议授权
    GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 

**权限说明**

* select：需要读取server端information_schema.COLUMNS表，获取表结构的元信息，拼接成可视化的sql语句
* super/replication client：两个权限都可以，需要执行'SHOW MASTER STATUS', 获取server端的binlog列表
* replication slave：通过BINLOG_DUMP协议获取binlog内容的权限


### 基本用法


**解析出标准SQL 附带时间 **

```bash
shell> PYTHONPATH=. ./bin/flashback -h 127.0.0.1 -p yaolu -u yaolu -T alembic_version --start-datetime='2018-01-20 20:09:27' --list

输出：
{'next_position': 24578505, 'timestamp': '2018-01-20 20:09:27', 'sql': 'delete from `jupiter`.`home` where id = 5', 'event_length': 76, 'position': 24578429}

{'timestamp': '2018-01-20 20:09:59', 'sql': 'insert into `jupiter`.`home`(`id`,`addr`,`aa`,`name`,`ab`,`deci`,`ae`,`ac`,`description`) values (5,"qkd",5,"gg",33.0,33.0,31,1.0,"g1")', 'position': 24578740}

{'timestamp': '2018-01-20 20:10:41', 'sql': 'insert into `jupiter`.`home`(`id`,`addr`,`aa`,`name`,`ab`,`deci`,`ae`,`ac`,`description`) values (6,"df",33,"ww",33.0,11.0,123,1.0,"dd")', 'position': 24579058}
```

**解析出回滚SQL**

```bash

shell> PYTHONPATH=. ./bin/flashback -h 127.0.0.1 -p yaolu -u yaolu -T alembic_version --start-datetime='2018-01-20 20:09:27' --rollback
无异常
输出空
```

### 选项

**mysql连接配置**

-h host; -P port; -u user; -p password

**解析模式**

-K, --no-primary-key 对INSERT语句去除主键。可选。默认False

--rollback 生成回滚sql 并执行

**解析范围控制**

--start-file 起始解析文件，只需文件名，无需全路径 。 不填默认执行 show master status 中的binlog 文件。

--start-pos 起始解析位置。可选。默认为start-file的起始位置。

--end-file 终止解析文件。可选。默认为start-file同一个文件。

--end-pos 终止解析位置。可选。默认为stop-file的最末位置

--start-datetime 起始解析时间，格式'%Y-%m-%d %H:%M:%S'。可选。默认不过滤。

--stop-datetime 终止解析时间，格式'%Y-%m-%d %H:%M:%S'。可选。默认不过滤。

**对象过滤**

-d, --databases 只解析目标db的sql，多个库用空格隔开，如-d db1 db2。可选。默认为空。

-D, --skip-databases 跳过目标 db。 可选

-t, --tables 只解析目标table的sql，多张表用空格隔开，如-t tbl1 tbl2。可选。默认为空。

-T, --skip-tables 跳过目标 table, 可选

--sql-type 只解析指定类型，支持INSERT, UPDATE, DELETE。多个类型用空格隔开，如--sql-type INSERT DELETE。可选。默认为增删改都解析。用了此参数但没填任何类型，则三者都不解析。


### 优点（对比mysqlbinlog）

* 纯Python开发，安装与使用都很简单
* 自带flashback、no-primary-key解析模式
* 解析为标准SQL，方便理解、筛选
* 代码容易改造，可以支持更多个性化解析

目前还有部分功能暂未开发完成， 近一两周完成， 支持普通的 DML 操作
