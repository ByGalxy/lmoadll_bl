create table lmoadll_users
(
    uid        INTEGER not null
        constraint key
            primary key,
    name       varchar(32)  default NULL,
    password   varchar(64)  default NULL,
    mail       varchar(150) default NULL,
    url        varchar(150) default NULL,
    createdAt  int(10)      default 0,
    isActive   int(10)      default 0,
    isLoggedIn int(10)      default 0,
    "group"    varchar(16)  default 'visitor'
);
