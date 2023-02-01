CREATE TABLE conform_spendings (
    id SERIAL NOT NULL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    start_date DATE,
    end_date DATE,
    resource_group varchar(40),
    amount FLOAT,
    source_system VARCHAR(10),
    tags varchar(20),
    region varchar(20)
);
CREATE OR REPLACE FUNCTION trigger_set_timestamp() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER set_timestamp BEFORE
UPDATE ON conform_spendings FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();