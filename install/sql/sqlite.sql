create table lmoadll_users
(
    uid        integer not null
        constraint key
            primary key,
    name       varchar(32)  default null,
    password   varchar(64)  default null,
    mail       varchar(150) default null,
    url        varchar(150) default null,
    createdAt  int(10)      default 0,
    isActive   int(10)      default 0,
    isLoggedIn int(10)      default 0,
    "group"    varchar(16)  default 'visitor'
);


create table lmoadll_options
(
    name  varchar(32)         not null,
    user  int(10) default '0' not null,
    value text
);

create unique index lmoadll_options__name_user
    on lmoadll_options (name, user);
