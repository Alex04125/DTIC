// src/GetVSValueForm.js

import React from "react";
import { useForm } from "react-hook-form";
import axios from "axios";
import styled from "styled-components";
import { ClipLoader } from "react-spinners";
import Modal from "react-modal";

const FormContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f4f8;
`;

const Form = styled.form`
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 400px;
`;

const FormGroup = styled.div`
  margin-bottom: 1rem;
`;

const Label = styled.label`
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
`;

const Error = styled.p`
  color: red;
  font-size: 0.875rem;
  margin-top: 0.25rem;
`;

const Button = styled.button`
  width: 100%;
  padding: 0.75rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #0056b3;
  }
`;

const ModalContent = styled.div`
  background: white;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const GetVSValueForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm();
  const [loading, setLoading] = React.useState(false);
  const [modalMessage, setModalMessage] = React.useState(null);
  const [modalIsOpen, setModalIsOpen] = React.useState(false);

  const onSubmit = async (data) => {
    setLoading(true);
    setModalMessage(null);
    try {
      const response = await axios.post("/api/get_vs_value", data);
      if (response.data.error) {
        setModalMessage(response.data.error);
      } else {
        setModalMessage("Request processed successfully!");
      }
      setModalIsOpen(true); // Open the modal
    } catch (error) {
      const errorMessage =
        error.response?.data?.error ||
        "An error occurred while processing the request.";
      setModalMessage(errorMessage);
      setModalIsOpen(true); // Open the modal on error
      console.error("There was an error processing the request!", error);
    } finally {
      setLoading(false);
      reset();
    }
  };

  const closeModal = () => {
    setModalIsOpen(false);
  };

  return (
    <FormContainer>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <FormGroup>
          <Label>Instance Name</Label>
          <Input {...register("instance_name", { required: true })} />
          {errors.instance_name && <Error>Instance name is required</Error>}
        </FormGroup>
        <FormGroup>
          <Label>GitHub URL</Label>
          <Input {...register("github_url", { required: true })} />
          {errors.github_url && <Error>GitHub URL is required</Error>}
        </FormGroup>
        <FormGroup>
          <Label>File Name</Label>
          <Input {...register("file_name", { required: true })} />
          {errors.file_name && <Error>File name is required</Error>}
        </FormGroup>
        <Button type="submit" disabled={loading}>
          {loading ? <ClipLoader size={20} color="#ffffff" /> : "Get VS Value"}
        </Button>
      </Form>
      <Modal
        isOpen={modalIsOpen}
        onRequestClose={closeModal}
        contentLabel="Request Status"
        ariaHideApp={false}
        style={{
          content: {
            top: "50%",
            left: "50%",
            right: "auto",
            bottom: "auto",
            marginRight: "-50%",
            transform: "translate(-50%, -50%)",
          },
        }}
      >
        <ModalContent>
          {modalMessage && modalMessage.includes("An error occurred") ? (
            <>
              <h2>Error</h2>
              <p>{modalMessage}</p>
            </>
          ) : (
            <>
              <h2>Success!</h2>
              <p>{modalMessage}</p>
              <p>
                You can check the VS Value on the{" "}
                <a href="/vs_values">VS Values</a> page.
              </p>
            </>
          )}
          <Button onClick={closeModal}>Close</Button>
        </ModalContent>
      </Modal>
    </FormContainer>
  );
};

export default GetVSValueForm;
