import {
  FaBroom,
  FaDna,
  FaFont,
  FaBrain,
  FaBullseye,
  FaChartLine,
} from "react-icons/fa";

// Pipeline steps configuration
export const PIPELINE_STEPS = [
  { id: 1, title: "Data", subtitle: "Preprocessing", icon: <FaBroom /> },
  { id: 2, title: "MSA", subtitle: "Alignment", icon: <FaDna /> },
  { id: 3, title: "Tokenisation", subtitle: "Encoding", icon: <FaFont /> },
  { id: 4, title: "Embedding", subtitle: "Representation", icon: <FaBrain /> },
  {
    id: 5,
    title: "Classification",
    subtitle: "Linear Probing",
    icon: <FaBullseye />,
  },
  { id: 6, title: "Evaluation", subtitle: "Analysis", icon: <FaChartLine /> },
];

// Step descriptions
export const STEP_DESCRIPTIONS = {
  1: "Data preprocessing involves cleaning DNA sequences and splitting them into 512bp windows for analysis.",
  2: "Multiple Sequence Alignment (MSA) aligns DNA from different species to identify conserved regions.",
  3: "Tokenisation converts DNA bases (A, T, C, G) into numerical representations for the model.",
  4: "Embedding transforms token sequences into high-dimensional vectors that capture biological patterns.",
  5: "The prediction model uses masked language modeling to predict missing bases in sequences.",
  6: "Evaluation uses UMAP clustering and accuracy metrics to assess model performance.",
};
