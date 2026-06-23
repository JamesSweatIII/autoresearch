import "../styles/globals.css";
import Layout from "../components/layout/Layout";
import WakeBackend from "../components/ui/WakeBackend";

export default function App({ Component, pageProps }) {
  return (
    <WakeBackend>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </WakeBackend>
  );
}
