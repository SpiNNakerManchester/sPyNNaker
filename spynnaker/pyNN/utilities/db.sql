-- Copyright (c) 2022 The University of Manchester
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.

-- We want foreign key enforcement; it should be default on, but it isn't for
-- messy historical reasons.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS population (
    pop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    first_id int NOT NULL,
    description TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS recording (
    rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_id INTEGER NOT NULL
		REFERENCES population(pop_id) ON DELETE RESTRICT,
    variable TEXT NOT NULL,
    data_type TEXT,
    function TEXT NOT NULL,
    t_start float NOT NULL,
    sampling_interval_ms float);

CREATE UNIQUE INDEX IF NOT EXISTS recording_sanity
    ON recording(pop_id ASC, variable ASC);

CREATE VIEW IF NOT EXISTS recording_view AS
    SELECT rec_id, variable, label, data_type, function, t_start,
        sampling_interval_ms, first_id
    FROM population NATURAL JOIN recording;

CREATE TABLE IF NOT EXISTS segment(
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_time_step_ms FLOAT NOT NULL,
    segment_number INTEGER NOT NULL,
    t_stop FLOAT,
    rec_datetime TIMESTAMP NOT NULL);

CREATE TABLE IF NOT EXISTS spikes_metadata(
    spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    neurons_st TEXT NOT NULL,
    selective_recording BOOLEAN NOT NULL);

CREATE TABLE IF NOT EXISTS eieio_spikes_metadata(
    eieio_spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    base_key INT NOT NULL,
    vertex_slice TEXT NOT NULL,
    atoms_shape TEXT NOT NULL,
    n_colour_bits INT NOT NULL);

CREATE TABLE IF NOT EXISTS multi_spikes_metadata(
    multi_spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    vertex_slice TEXT NOT NULL,
    atoms_shape TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS matrix_metadata(
    spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    neurons_st TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS rewires_metadata(
    rewires_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER NOT NULL
		REFERENCES recording(rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    vertex_slice TEXT NOT NULL);