// src/components/MetricCard.tsx
import { Card, Heading, Text, Spinner, Flex } from "@chakra-ui/react";

type Props = {
  title: string;
  value?: number | string;
  loading?: boolean;
  note?: string;
};

export default function MetricCard({ title, value, loading, note }: Props) {
  return (
    <Card.Root p="4" borderWidth="1px">
      <Card.Header>
        <Heading size="sm">{title}</Heading>
      </Card.Header>
      <Card.Body>
        <Flex align="center" minH="48px">
          {loading ? <Spinner /> : <Heading size="lg">{value ?? "—"}</Heading>}
        </Flex>
        {note && (
          <Text mt="2" color="fg.muted" fontSize="sm">
            {note}
          </Text>
        )}
      </Card.Body>
    </Card.Root>
  );
}
