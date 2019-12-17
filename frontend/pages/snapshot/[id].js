import { useRouter } from 'next/router';
import Layout from '../layout';
import Link from 'next/link';
import fetch from 'isomorphic-unfetch';

const Snapshot = props => {
  const router = useRouter();

  return (
    <Layout>
      <h1>{router.query.id}</h1>
      <ul>
        {props.posts.map(post => (
          <li key={post.title}>
            <Link href="/snapshot/post/[id]" as={`/snapshot/post/${post.title}`}>
              <a>{post.title}</a>
            </Link>
          </li>
        ))}
      </ul>
    </Layout>
  );
}

Snapshot.getInitialProps = async function(context) {
  const { id } = context.query;
  const res = await fetch(`http://127.0.0.1:5000/api/V1/getposts?utctimestamp=${id}`);
  const posts = await res.json();

  console.log(`Show data fetched. Count: ${posts.length}`);

  return {
    posts
  };
};

export default Snapshot
