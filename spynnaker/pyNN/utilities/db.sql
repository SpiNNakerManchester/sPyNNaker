-- Copyright (c) 2022-2023 The University of Manchester
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- We want foreign key enforcement; it should be default on, but it isn't for
-- messy historical reasons.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS population (
    pop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    first_id int NOT NULL,
    pop_size int NOT NULL,
    description TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS recording (
    rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_id INTEGER NOT NULL
		REFERENCES population(pop_id) ON DELETE RESTRICT,
    variable TEXT NOT NULL,
    data_type TEXT,
    buffered_type TEXT NOT NULL,
    t_start float NOT NULL,
    sampling_interval_ms float,
    units TEXT,
    atoms_shape TEXT,
    n_colour_bits INT);

CREATE UNIQUE INDEX IF NOT EXISTS recording_sanity
    ON recording(pop_id ASC, variable ASC);

CREATE VIEW IF NOT EXISTS recording_view AS
    SELECT rec_id, variable, label, data_type, buffered_type, t_start,
        sampling_interval_ms, pop_size, units, atoms_shape, n_colour_bits
    FROM population NATURAL JOIN recording;

CREATE TABLE IF NOT EXISTS segment(
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_time_step_ms FLOAT NOT NULL,
    segment_number INTEGER NOT NULL,
    rec_datetime TIMESTAMP NOT NULL,
    t_stop FLOAT,
    dt FLOAT NOT NULL,
    simulator STRING NOT NULL);

CREATE TABLE IF NOT EXISTS region_metadata(
    region_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    recording_neurons_st TEXT,
    vertex_slice TEXT,
    base_key INT);

