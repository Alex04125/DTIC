// src/App.js

import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import CreateInstanceForm from "./CreateInstanceForm";
import UploadModuleForm from "./UploadModuleForm";
import GetVSValueForm from "./GetVSValueForm";
import ModulesPage from "./ModulesPage";
import InstancesPage from "./InstancesPage";
import Navbar from "./Navbar";
import GlobalStyle from "./GlobalStyle";
import styled from "styled-components";

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const Home = styled.div`
  margin-top: 2rem;
  text-align: center;
`;

const App = () => {
  return (
    <Router>
      <AppContainer>
        <GlobalStyle />
        <Navbar />
        <Routes>
          <Route
            path="/"
            element={
              <Home>
                <h1>Welcome to Our Services</h1>
                <p>Select a service from the navigation bar above.</p>
              </Home>
            }
          />
          <Route path="/create-instance" element={<CreateInstanceForm />} />
          <Route path="/upload-module" element={<UploadModuleForm />} />
          <Route path="/get-vs-value" element={<GetVSValueForm />} />
          <Route path="/modules" element={<ModulesPage />} />
          <Route path="/instances" element={<InstancesPage />} />
        </Routes>
      </AppContainer>
    </Router>
  );
};

export default App;
