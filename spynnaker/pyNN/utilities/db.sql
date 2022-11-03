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

CREATE TABLE IF NOT EXISTS population_recording (
    pop_rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    variable TEXT NOT NULL,
    data_type TEXT NOT NULL,
    function TEXT NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS population_recording_sanity
    ON population_recording(label ASC, variable ASC);

CREATE TABLE IF NOT EXISTS segment(
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_time_step_ms FLOAT NOT NULL);

CREATE TABLE IF NOT EXISTS spikes_metadata(
    spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_rec_id INTEGER NOT NULL
		REFERENCES population_recording(pop_rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    neurons_st TEXT NOT NULL,
    simple_indexes BOOLEAN NOT NULL);

CREATE TABLE IF NOT EXISTS eieio_spikes_metadata(
    eieio_spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_rec_id INTEGER NOT NULL
		REFERENCES population_recording(pop_rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    base_key INT NOT NULL,
    vertex_slice TEXT NOT NULL,
    atoms_shape TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS multi_spikes_metadata(
    multi_spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_rec_id INTEGER NOT NULL
		REFERENCES population_recording(pop_rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    vertex_slice TEXT NOT NULL,
    atoms_shape TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS matrix_metadata(
    spikes_metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pop_rec_id INTEGER NOT NULL
		REFERENCES population_recording(pop_rec_id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL
		REFERENCES region(region_id) ON DELETE RESTRICT,
    neurons_st TEXT NOT NULL,
    sampling_rate float NOT NULL);
