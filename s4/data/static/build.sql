CREATE TABLE IF NOT EXISTS bot (
    Key text PRIMARY KEY,
    Value text
);

INSERT OR IGNORE INTO bot VALUES ("last commit", CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS errors (
    Ref text PRIMARY KEY,
    ErrorTime text DEFAULT CURRENT_TIMESTAMP,
    Content text,
    Traceback text
);

CREATE TABLE IF NOT EXISTS system (
    GuildID integer PRIMARY KEY,
    RunFTS integer DEFAULT 0,
    Prefix text DEFAULT ">>",
    DefaultLogChannelID integer,
    LogChannelID integer,
    DefaultAdminRoleID interger,
    AdminRoleID integer
);
