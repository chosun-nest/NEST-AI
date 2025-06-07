import { FC, memo } from 'react';
import ReactMarkdown, { Options } from 'react-markdown';

// className도 팔로업해야 한다.
export const MemoizedReactMarkdown:FC<Options> = memo(ReactMarkdown, (prevProps, nextProps) => {
    return prevProps.children === nextProps.children && prevProps.className === nextProps.className
})
