-- The warehouse's picking feed. The service writes one row per pick; the
-- warehouse picks whatever is here, so two rows for one order are two
-- boxes packed. The harness counts rows, and nothing here stops a duplicate.
CREATE TABLE picks (
    id        bigserial PRIMARY KEY,
    event_id  text NOT NULL,
    order_id  text NOT NULL,
    picked_at timestamptz NOT NULL DEFAULT now()
);
