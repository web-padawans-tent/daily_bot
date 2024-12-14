CREATE TABLE users(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	userid BIGINT NOT NULL,
	username VARCHAR(255),
	first_name varchar(255),
	fullname varchar(255),
	phone varchar(255),
	active boolean
);
CREATE TABLE subs(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	subsuser INTEGER REFERENCES users(id),
	start_sub TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	next_sub TIMESTAMP,
	pay_method varchar(255),
	tried_pay integer
);
