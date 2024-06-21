// src/Navbar.js

import React from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const Nav = styled.nav`
  background: #007bff;
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const NavLink = styled(Link)`
  color: white;
  font-size: 1.2rem;
  margin: 0 1rem;
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
`;

const Navbar = () => {
  return (
    <Nav>
      <NavLink to="/">Home</NavLink>
      <NavLink to="/create-instance">Create Instance</NavLink>
      <NavLink to="/upload-module">Upload Module</NavLink>
      <NavLink to="/get-vs-value">Get VS Value</NavLink>
      <NavLink to="/modules">Modules</NavLink>
      <NavLink to="/instances">Instances</NavLink>
    </Nav>
  );
};

export default Navbar;
