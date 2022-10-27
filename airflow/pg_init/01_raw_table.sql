CREATE TABLE raw_data (
    id SERIAL NOT NULL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data JSON,
    source_system VARCHAR(10)
);
CREATE OR REPLACE FUNCTION trigger_set_timestamp() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER set_timestamp BEFORE
UPDATE ON raw_data FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();