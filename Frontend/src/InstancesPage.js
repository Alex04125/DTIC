// src/InstancesPage.js

import React, { useState } from "react";
import axios from "axios";
import styled from "styled-components";

const PageContainer = styled.div`
  padding: 2rem;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
`;

const Th = styled.th`
  border: 1px solid #ddd;
  padding: 8px;
  background-color: #f2f2f2;
`;

const Td = styled.td`
  border: 1px solid #ddd;
  padding: 8px;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  margin-top: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
`;

const Button = styled.button`
  padding: 0.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
  margin-right: 1rem;

  &:hover {
    background-color: #0056b3;
  }
`;

const InstancesPage = () => {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchAllInstances = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get("/api/instances");
      setInstances(response.data);
    } catch (err) {
      setError("Error fetching instances");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/instances/${searchTerm}`);
      setInstances([response.data]);
    } catch (err) {
      setError("Instance not found");
      setInstances([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      <h1>Instances</h1>
      <div>
        <Button onClick={fetchAllInstances} disabled={loading}>
          {loading ? "Loading..." : "Get All Instances"}
        </Button>
      </div>
      <Input
        type="text"
        placeholder="Search instance by name"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <Button onClick={handleSearch} disabled={loading}>
        {loading ? "Loading..." : "Search"}
      </Button>
      {error && <p>{error}</p>}
      <Table>
        <thead>
          <tr>
            <Th>Instance Name</Th>
            <Th>Module Name</Th>
            <Th>Status</Th>
            <Th>Container Status</Th>
          </tr>
        </thead>
        <tbody>
          {instances.map((instance) => (
            <tr key={instance.id}>
              <Td>{instance.instance_name}</Td>
              <Td>{instance.module_name}</Td>
              <Td>{instance.status}</Td>
              <Td>{instance.container_status}</Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </PageContainer>
  );
};

export default InstancesPage;
