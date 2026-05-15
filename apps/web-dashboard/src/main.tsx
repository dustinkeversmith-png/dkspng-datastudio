import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import ApiIntakeLab from "./ApiIntakeLab";
import "./styles.css";

const pathname = window.location.pathname.toLowerCase();
const RootComponent = pathname === "/lab" ? ApiIntakeLab : App;

createRoot(document.getElementById("root")!).render(<RootComponent />);
