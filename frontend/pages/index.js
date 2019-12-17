// This is the Link API
import Layout from './layout'
import Link from 'next/link';
import fetch from 'isomorphic-unfetch';

const Index = props => (
  <Layout>
    <h1>Reddit Snapshots</h1>
    <ul>
      {props.snapshots.map(snapshot=> (
        <li key={snapshot.utctimestamp}>
          <Link href="/snapshot/[id]" as={`/snapshot/${snapshot.utctimestamp}`}>
            <a>{snapshot.subreddit} - {snapshot.utctimestamp}</a>
          </Link>
        </li>
      ))}
    </ul>
  </Layout>
);

Index.getInitialProps = async function() {
  const res = await fetch('http://127.0.0.1:5000/api/V1/snapshot');
  const snapshots = await res.json();

  console.log(`Show data fetched. Count: ${snapshots.length}`);

  return {
    snapshots
  };
};

export default Index;

